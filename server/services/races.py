"""Race calendar and race-weekend status.

Status lifecycle for a race weekend:
- ``upcoming``  — before lockdown; team changes allowed.
- ``lockdown``  — from lockdown (first competitive session) until the race is
  scored; no team changes. Qualifying and sprint results may already be in
  (scored live, see services/results.py).
- ``completed`` — the race's own result is in.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models import DriverResult, Race

UPCOMING = "upcoming"
LOCKDOWN = "lockdown"
COMPLETED = "completed"


def utcnow() -> datetime:
    # Naive UTC, matching how DateTime columns round-trip through SQLite.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def race_status(race: Race, has_results: bool, now: datetime) -> str:
    """Pure status rule — see module docstring."""
    if has_results:
        return COMPLETED
    if race.lockdown_at is not None and race.lockdown_at <= now:
        return LOCKDOWN
    return UPCOMING


def races_with_results(db: Session, race_ids: list[int] | None = None) -> set[int]:
    """Ids of races whose race result is in. Qualifying/sprint-only results
    (stored before the race) don't count."""
    q = db.query(DriverResult.race_id).filter(DriverResult.race_pos.is_not(None)).distinct()
    if race_ids is not None:
        q = q.filter(DriverResult.race_id.in_(race_ids))
    return {race_id for (race_id,) in q}


def list_races(db: Session, season: int) -> list[Race]:
    return db.query(Race).filter_by(season=season).order_by(Race.round).all()


def get_race(db: Session, race_id: int) -> Race | None:
    return db.get(Race, race_id)


def get_race_by_round(db: Session, season: int, rnd: int) -> Race | None:
    return db.query(Race).filter_by(season=season, round=rnd).one_or_none()


def next_race(races: list[Race], with_results: set[int]) -> Race | None:
    """The first race (by round) that hasn't been completed."""
    return next((r for r in races if r.id not in with_results), None)


def current_race(db: Session, season: int) -> Race | None:
    """The race weekend team changes currently apply to: the first race that
    isn't completed. None once the season is over."""
    races = list_races(db, season)
    return next_race(races, races_with_results(db, [r.id for r in races]))
