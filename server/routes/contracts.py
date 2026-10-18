"""The signed-in user's team: list, sign and release contracts."""

from fastapi import APIRouter, HTTPException, status

from config import settings
from dependencies import CurrentUser, DbSession
from models import Contract, Driver, LeagueMember, Race
from schemas.contracts import (
    ContractCreate,
    ContractListResponse,
    ContractResponse,
    CooldownElement,
    CurrentRace,
    ReleaseResponse,
)
from services import contracts as contract_service
from services import races as race_service

router = APIRouter(prefix="/contracts", tags=["contracts"])


def contract_response(db: DbSession, contract: Contract, current: Race | None) -> ContractResponse:
    element = contract_service.get_element(db, contract.element_type, contract.element_id)
    is_driver = isinstance(element, Driver)
    current_round = current.round if current else contract.race_start
    locked = bool(current and current.lockdown_at and current.lockdown_at <= race_service.utcnow())
    end = contract_service.last_round(contract)
    return ContractResponse(
        id=contract.id,
        element_type=contract.element_type,
        element_id=contract.element_id,
        element_name=element.name if element else "Unknown",
        element_color=(element.constructor.color if is_driver else element.color) if element else None,
        constructor_name=element.constructor.name if is_driver else None,
        signed_salary=contract.signed_salary,
        current_salary=element.salary if element else contract.signed_salary,
        race_start=contract.race_start,
        contract_length=contract.contract_length,
        last_round=end,
        races_remaining=end - current_round + 1,
        cancellable=contract.race_start >= current_round and not locked,
    )


def _member_or_403(db: DbSession, user: CurrentUser) -> LeagueMember:
    member = contract_service.get_membership(db, user)
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You're not a member of the league")
    return member


@router.get("", response_model=ContractListResponse)
def list_contracts(user: CurrentUser, db: DbSession) -> ContractListResponse:
    member = _member_or_403(db, user)
    current = race_service.current_race(db, settings.season)
    contracts = contract_service.roster_contracts(db, member, current.round if current else None)
    items = [contract_response(db, c, current) for c in contracts]
    contract_value = sum(c.current_salary for c in items)
    current_race = None
    cooldown: list[CooldownElement] = []
    if current is not None:
        races_left = db.query(Race).filter(Race.season == settings.season, Race.round >= current.round).count()
        current_race = CurrentRace(
            id=current.id, round=current.round, name=current.name, lockdown_at=current.lockdown_at,
            locked=bool(current.lockdown_at and current.lockdown_at <= race_service.utcnow()),
            races_left=races_left,
        )
        cooldown = [CooldownElement(element_type=t, element_id=i)
                    for t, i in contract_service.cooldown_elements(db, member, current.round)]
    return ContractListResponse(
        contracts=sorted(items, key=lambda c: (c.element_type.value != "driver", -c.current_salary)),
        bank_balance=member.bank_balance,
        contract_value=contract_value,
        team_value=member.bank_balance + contract_value,
        current_race=current_race,
        cooldown=cooldown,
    )


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def sign(body: ContractCreate, user: CurrentUser, db: DbSession) -> ContractResponse:
    try:
        contract = contract_service.sign_contract(
            db, user, body.element_type, body.element_id, body.contract_length,
            season=settings.season, now=race_service.utcnow(),
        )
    except contract_service.InsufficientFunds as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    except contract_service.ContractConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    db.commit()
    return contract_response(db, contract, race_service.current_race(db, settings.season))


@router.delete("/{contract_id}", response_model=ReleaseResponse)
def release(contract_id: int, user: CurrentUser, db: DbSession) -> ReleaseResponse:
    try:
        result = contract_service.release_contract(
            db, user, contract_id, season=settings.season, now=race_service.utcnow()
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    db.commit()
    return ReleaseResponse(released=True, penalty=result.penalty, refund=result.refund,
                           bank_balance=result.bank_balance)
