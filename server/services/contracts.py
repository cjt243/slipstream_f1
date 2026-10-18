"""Contracts: signing, early release, expiry (LEAGUE_MECHANICS.md §5–§6).

Money model (settle on release): signing moves the element's current salary
from cash into the contract; when the contract ends — early release or expiry
— the element's *current* (post-race) salary comes back as cash, less a 3%
penalty on early release. Team value = cash + current salaries under contract.

Timing: team changes apply to the *current race* (the first race not yet
completed) and are only allowed before its lockdown. A contract covers rounds
``race_start`` … ``race_start + contract_length − 1``. Releasing a contract
whose first race hasn't locked yet is a free cancellation (full refund, no
cooldown) — it was never really signed. After any departure the element can't
be re-signed for the next race (one-race interval).

Star driver: before lockdown a user may pick one of their drivers earning
under STAR_MAX_SALARY as the current race's star; its points count double
(services/fantasy.py). Picked afresh each race.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from models import (
    Constructor,
    Contract,
    Driver,
    ElementType,
    League,
    LeagueMember,
    Race,
    StarDriver,
    User,
)
from services import races as race_service
from services.seed import DEFAULT_LEAGUE_INVITE_CODE

MIN_LENGTH = 1
MAX_LENGTH = 5
MAX_ON_ROSTER = {ElementType.DRIVER: 5, ElementType.CONSTRUCTOR: 1}
RELEASE_PENALTY_RATE = 0.03
STAR_MAX_SALARY = 18_000_000  # a star driver must earn less than this


class ContractConflict(ValueError):
    """Already signed, or in the post-release cooldown (HTTP 409)."""


class InsufficientFunds(ValueError):
    """Not enough cash to sign (HTTP 402)."""


@dataclass(frozen=True)
class Release:
    penalty: int
    refund: int
    bank_balance: int


def last_round(contract: Contract) -> int:
    return contract.race_start + contract.contract_length - 1


def get_membership(db: Session, user: User) -> LeagueMember | None:
    """The user's membership (and cash) in the default league."""
    return (
        db.query(LeagueMember)
        .join(League)
        .filter(League.invite_code == DEFAULT_LEAGUE_INVITE_CODE, LeagueMember.user_id == user.id)
        .one_or_none()
    )


def get_element(db: Session, element_type: ElementType, element_id: int) -> Driver | Constructor | None:
    model = Driver if element_type == ElementType.DRIVER else Constructor
    return db.get(model, element_id)


def roster_contracts(db: Session, member: LeagueMember, current_round: int | None) -> list[Contract]:
    """Contracts on the member's team for the current race (not released, not
    yet past their last round). Empty once the season is over."""
    if current_round is None:
        return []
    rows = (
        db.query(Contract)
        .filter(Contract.user_id == member.user_id, Contract.league_id == member.league_id,
                Contract.released_at_race.is_(None))
        .all()
    )
    return [c for c in rows if last_round(c) >= current_round]


def cooldown_elements(db: Session, member: LeagueMember, current_round: int) -> set[tuple[ElementType, int]]:
    """Elements that left this team after the previous race and so can't be
    signed for the current one."""
    rows = (
        db.query(Contract.element_type, Contract.element_id)
        .filter(Contract.user_id == member.user_id, Contract.league_id == member.league_id,
                Contract.released_at_race == current_round - 1)
        .all()
    )
    return {(ElementType(t), i) for t, i in rows}


def _require_open_race(db: Session, season: int, now: datetime) -> Race:
    race = race_service.current_race(db, season)
    if race is None:
        raise ValueError("The season is over")
    if race.lockdown_at is not None and race.lockdown_at <= now:
        raise ValueError(f"Lockdown is active for the {race.name} — team changes reopen after the race")
    return race


def sign_contract(db: Session, user: User, element_type: ElementType, element_id: int,
                  length: int, *, season: int, now: datetime) -> Contract:
    member = get_membership(db, user)
    if member is None:
        raise PermissionError("You're not a member of the league")
    if not MIN_LENGTH <= length <= MAX_LENGTH:
        raise ValueError(f"Contract length must be {MIN_LENGTH}–{MAX_LENGTH} races")
    element = get_element(db, element_type, element_id)
    if element is None or element.season != season:
        raise LookupError("No such driver or constructor this season")
    if isinstance(element, Driver) and not element.is_active:
        raise ValueError(f"{element.name} isn't on the current grid")

    race = _require_open_race(db, season, now)
    races_left = db.query(Race).filter(Race.season == season, Race.round >= race.round).count()
    if length > races_left:
        raise ValueError(f"Only {races_left} race{'s' if races_left != 1 else ''} left this season")

    roster = roster_contracts(db, member, race.round)
    if any(c.element_type == element_type and c.element_id == element_id for c in roster):
        raise ContractConflict(f"{element.name} is already on your team")
    if (element_type, element_id) in cooldown_elements(db, member, race.round):
        raise ContractConflict(f"{element.name} just left your team — you can sign them again after this race")
    if sum(c.element_type == element_type for c in roster) >= MAX_ON_ROSTER[element_type]:
        kind = "drivers" if element_type == ElementType.DRIVER else "constructor"
        raise ValueError(f"Your team already has {MAX_ON_ROSTER[element_type]} {kind}")
    if member.bank_balance < element.salary:
        raise InsufficientFunds(f"Not enough cash to sign {element.name}")

    member.bank_balance -= element.salary
    contract = Contract(
        user_id=user.id, league_id=member.league_id, element_type=element_type,
        element_id=element_id, race_start=race.round, contract_length=length,
        signed_salary=element.salary,
    )
    db.add(contract)
    db.flush()
    return contract


def release_contract(db: Session, user: User, contract_id: int, *, season: int,
                     now: datetime) -> Release | None:
    """Release one of the user's roster contracts. None if it isn't theirs or
    isn't on their team."""
    member = get_membership(db, user)
    contract = db.get(Contract, contract_id)
    if member is None or contract is None or contract.user_id != user.id:
        return None
    race = race_service.current_race(db, season)
    if race is None or contract not in roster_contracts(db, member, race.round):
        return None
    race = _require_open_race(db, season, now)
    element = get_element(db, contract.element_type, contract.element_id)
    current_salary = element.salary if element else contract.signed_salary

    if contract.element_type == ElementType.DRIVER:
        star = get_star(db, member, race)
        if star is not None and star.driver_id == contract.element_id:
            db.delete(star)

    if contract.race_start >= race.round:
        # Hasn't raced yet: free cancellation.
        member.bank_balance += contract.signed_salary
        db.delete(contract)
        db.flush()
        return Release(penalty=0, refund=contract.signed_salary, bank_balance=member.bank_balance)

    penalty = round(current_salary * RELEASE_PENALTY_RATE)
    refund = current_salary - penalty
    member.bank_balance += refund
    contract.released_early = True
    contract.released_at_race = race.round - 1  # last round served
    db.flush()
    return Release(penalty=penalty, refund=refund, bank_balance=member.bank_balance)


def get_star(db: Session, member: LeagueMember, race: Race) -> StarDriver | None:
    return (
        db.query(StarDriver)
        .filter_by(user_id=member.user_id, league_id=member.league_id, race_id=race.id)
        .one_or_none()
    )


def set_star_driver(db: Session, user: User, driver_id: int, *, season: int,
                    now: datetime) -> StarDriver:
    """Make one of the user's drivers their star for the current race,
    replacing any earlier pick."""
    member = get_membership(db, user)
    if member is None:
        raise PermissionError("You're not a member of the league")
    driver = db.get(Driver, driver_id)
    if driver is None or driver.season != season:
        raise LookupError("No such driver this season")
    race = _require_open_race(db, season, now)
    if not any(c.element_type == ElementType.DRIVER and c.element_id == driver_id
               for c in roster_contracts(db, member, race.round)):
        raise ValueError(f"{driver.name} isn't on your team")
    if driver.salary >= STAR_MAX_SALARY:
        raise ValueError(f"Star drivers must earn under £{STAR_MAX_SALARY // 1_000_000}M")

    star = get_star(db, member, race) or StarDriver(
        user_id=user.id, league_id=member.league_id, race_id=race.id, driver_id=driver_id
    )
    star.driver_id = driver_id
    db.add(star)
    db.flush()
    return star


def clear_star_driver(db: Session, user: User, *, season: int, now: datetime) -> None:
    """Remove the user's star pick for the current race (no-op if none)."""
    member = get_membership(db, user)
    if member is None:
        raise PermissionError("You're not a member of the league")
    race = _require_open_race(db, season, now)
    star = get_star(db, member, race)
    if star is not None:
        db.delete(star)
        db.flush()


def settle_expired_contracts(db: Session, race: Race) -> int:
    """After ``race`` is scored and salaries adjusted, pay out contracts whose
    last round was this race at the element's post-race salary. Idempotent."""
    # Contracts store rounds, not seasons — fine while the league plays one season.
    rows = db.query(Contract).filter(Contract.released_at_race.is_(None)).all()
    expired = [c for c in rows if last_round(c) == race.round]
    for c in expired:
        member = (
            db.query(LeagueMember)
            .filter_by(league_id=c.league_id, user_id=c.user_id)
            .one_or_none()
        )
        element = get_element(db, c.element_type, c.element_id)
        if member is not None:
            member.bank_balance += element.salary if element else c.signed_salary
        c.released_at_race = race.round
    db.flush()
    return len(expired)
