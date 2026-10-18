"""Post-race salary adjustment (LEAGUE_MECHANICS.md §12).

After a race is scored, drivers and constructors are each ranked by fantasy
points; every element's salary moves a quarter of the way toward the default
salary for its rank (rounded toward zero to £100k, capped at ±£2M drivers /
±£3M constructors, at least ±£100k when any move is warranted).

Races are adjusted exactly once, in round order, so replaying a season is
deterministic. Under the league's settle-on-release bank model, salary
changes move team value, not bank balances.
"""

from sqlalchemy.orm import Session

from data.salaries import CONSTRUCTOR_DEFAULT_SALARY, DRIVER_DEFAULT_SALARY
from models import (
    Constructor,
    ConstructorResult,
    ConstructorScore,
    Driver,
    DriverResult,
    DriverScore,
    ElementType,
    Race,
    SalaryHistory,
)

MAX_ADJUSTMENT = {ElementType.DRIVER: 2_000_000, ElementType.CONSTRUCTOR: 3_000_000}
MIN_ADJUSTMENT = 100_000
STEP = 100_000


def adjusted_salary(current: int, rank: int, element_type: ElementType) -> int:
    """New salary for an element that finished ``rank`` by fantasy points."""
    table = DRIVER_DEFAULT_SALARY if element_type == ElementType.DRIVER else CONSTRUCTOR_DEFAULT_SALARY
    target = table[min(rank, max(table))]
    variation = target - current
    adjustment = int(variation / 4 / STEP) * STEP  # toward zero, to £100k
    cap = MAX_ADJUSTMENT[element_type]
    adjustment = max(-cap, min(cap, adjustment))
    if adjustment == 0 and variation != 0:
        adjustment = MIN_ADJUSTMENT if variation > 0 else -MIN_ADJUSTMENT
    return current + adjustment


def rank_by_points(points: list[tuple[int, int, int | None]]) -> dict[int, int]:
    """Rank (element_id, total_pts, finish_pos) by points, ties to the better finish."""
    ordered = sorted(points, key=lambda p: (-p[1], p[2] if p[2] is not None else 999, p[0]))
    return {element_id: rank for rank, (element_id, _, _) in enumerate(ordered, start=1)}


def is_adjusted(db: Session, race: Race) -> bool:
    return db.query(SalaryHistory.id).filter_by(race_id=race.id).first() is not None


def _is_scored(db: Session, race: Race) -> bool:
    return db.query(DriverScore.id).filter_by(race_id=race.id).first() is not None


def pending_earlier_race(db: Session, race: Race) -> Race | None:
    """The first earlier scored race in the season that still needs adjusting."""
    earlier = (
        db.query(Race)
        .filter(Race.season == race.season, Race.round < race.round)
        .order_by(Race.round)
        .all()
    )
    return next((r for r in earlier if _is_scored(db, r) and not is_adjusted(db, r)), None)


def adjust_salaries(db: Session, race: Race) -> int:
    """Apply the race's salary adjustments and record them. Returns the number
    of elements adjusted. Raises ValueError if the race isn't scored, was
    already adjusted, or an earlier race is still waiting."""
    if not _is_scored(db, race):
        raise ValueError("Race has not been scored yet")
    if is_adjusted(db, race):
        raise ValueError("Salaries were already adjusted for this race")
    pending = pending_earlier_race(db, race)
    if pending is not None:
        raise ValueError(f"Adjust round {pending.round} ({pending.name}) first")

    count = 0
    driver_rows = (
        db.query(DriverScore.driver_id, DriverScore.total_pts, DriverResult.race_pos)
        .outerjoin(DriverResult, (DriverResult.race_id == DriverScore.race_id)
                   & (DriverResult.driver_id == DriverScore.driver_id))
        .filter(DriverScore.race_id == race.id)
        .all()
    )
    for driver_id, rank in rank_by_points([tuple(r) for r in driver_rows]).items():
        driver = db.get(Driver, driver_id)
        count += _apply(db, race, ElementType.DRIVER, driver, rank)

    team_rows = (
        db.query(ConstructorScore.constructor_id, ConstructorScore.total_pts, ConstructorResult.race_pos)
        .outerjoin(ConstructorResult, (ConstructorResult.race_id == ConstructorScore.race_id)
                   & (ConstructorResult.constructor_id == ConstructorScore.constructor_id))
        .filter(ConstructorScore.race_id == race.id)
        .all()
    )
    for constructor_id, rank in rank_by_points([tuple(r) for r in team_rows]).items():
        team = db.get(Constructor, constructor_id)
        count += _apply(db, race, ElementType.CONSTRUCTOR, team, rank)
    db.flush()
    return count


def _apply(db: Session, race: Race, element_type: ElementType,
           element: Driver | Constructor | None, rank: int) -> int:
    if element is None:
        return 0
    before = element.salary
    element.salary = adjusted_salary(before, rank, element_type)
    db.add(SalaryHistory(element_type=element_type, element_id=element.id, race_id=race.id,
                         salary_before=before, salary_after=element.salary))
    return 1


def latest_changes(db: Session, element_type: ElementType) -> dict[int, int]:
    """Each element's most recent salary change (after − before), by element id."""
    rows = (
        db.query(SalaryHistory.element_id, SalaryHistory.salary_before, SalaryHistory.salary_after)
        .join(Race, Race.id == SalaryHistory.race_id)
        .filter(SalaryHistory.element_type == element_type)
        .order_by(Race.season, Race.round)
        .all()
    )
    return {element_id: after - before for element_id, before, after in rows}
