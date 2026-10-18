"""Initial season seeding from OpenF1 + static salary data.

Idempotent: every function checks for an existing row by its natural key before
inserting, and never truncates. Re-running ``seed_all`` is safe — it fills gaps
and refreshes race scheduling fields without clobbering salaries that may have
since been adjusted by the scoring engine.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from data.salaries import starting_constructor_salary, starting_driver_salary
from models import Constructor, Driver, League, Race
from services.openf1 import OpenF1Client

DEFAULT_LEAGUE_NAME = "Slipstream League"
DEFAULT_LEAGUE_INVITE_CODE = "SLIPSTREAM"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def seed_default_league(db: Session) -> League:
    league = db.query(League).filter_by(invite_code=DEFAULT_LEAGUE_INVITE_CODE).one_or_none()
    if league is None:
        league = League(name=DEFAULT_LEAGUE_NAME, invite_code=DEFAULT_LEAGUE_INVITE_CODE)
        db.add(league)
        db.flush()
    return league


def seed_constructors(db: Session, drivers_data: list[dict], season: int) -> dict[str, Constructor]:
    """Create constructors from the unique teams in the driver feed."""
    existing = {c.name: c for c in db.query(Constructor).filter_by(season=season)}
    for d in drivers_data:
        team = d.get("team_name")
        if not team:
            continue
        c = existing.get(team)
        if c is None:
            c = Constructor(
                name=team,
                salary=starting_constructor_salary(season, team),
                season=season,
            )
            db.add(c)
            existing[team] = c
        if d.get("team_color"):
            c.color = d["team_color"]
    db.flush()
    return existing


def upsert_driver(
    db: Session, d: dict, season: int, constructors: dict[str, Constructor]
) -> Driver | None:
    """Create a driver at their starting salary, or refresh an existing one's
    identity and team (mid-season seat changes). Salary is never touched on an
    existing driver — the salary engine owns it after creation."""
    num = d.get("driver_number")
    team = d.get("team_name")
    if num is None or team not in constructors:
        return None
    driver = db.query(Driver).filter_by(season=season, driver_number=num).one_or_none()
    if driver is None:
        driver = Driver(
            driver_number=num,
            salary=starting_driver_salary(season, d.get("code")),
            season=season,
        )
        db.add(driver)
    driver.name = d.get("name") or driver.name
    driver.code = d.get("code") or driver.code
    driver.constructor_id = constructors[team].id
    return driver


def seed_drivers(
    db: Session, drivers_data: list[dict], season: int, constructors: dict[str, Constructor]
) -> list[Driver]:
    drivers = [upsert_driver(db, d, season, constructors) for d in drivers_data]
    db.flush()
    return [d for d in drivers if d is not None]


def seed_races(db: Session, races_data: list[dict], season: int) -> list[Race]:
    """Upsert races by OpenF1 meeting_key (falling back to round)."""
    rows = list(db.query(Race).filter_by(season=season))
    by_meeting = {r.meeting_key: r for r in rows if r.meeting_key is not None}
    by_round = {r.round: r for r in rows}
    result: list[Race] = []
    for rd in races_data:
        race = by_meeting.get(rd.get("meeting_key")) or by_round.get(rd["round"])
        if race is None:
            race = Race(season=season, round=rd["round"])
            db.add(race)
        # Scheduling/identifier fields are safe to refresh on re-seed.
        race.round = rd["round"]
        race.name = rd.get("name")
        race.circuit = rd.get("circuit")
        race.has_sprint = bool(rd.get("has_sprint"))
        race.lockdown_at = _parse_dt(rd.get("lockdown_at"))
        race.meeting_key = rd.get("meeting_key")
        race.quali_session_key = rd.get("quali_session_key")
        race.sprint_session_key = rd.get("sprint_session_key")
        race.race_session_key = rd.get("race_session_key")
        result.append(race)
    db.flush()
    return result


def _representative_session_key(races_data: list[dict], now: datetime | None = None) -> int | str:
    """A session_key from this season so the driver feed matches the season
    (using 'latest' would return whatever session is most recent overall).

    Uses the most recent weekend that has already started, so the roster
    reflects the current grid; before the season starts, the first weekend."""
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    started = [rd for rd in races_data if (_parse_dt(rd.get("lockdown_at")) or now) < now]
    for rd in list(reversed(started)) + races_data:
        for key in ("race_session_key", "quali_session_key", "sprint_session_key"):
            if rd.get(key):
                return rd[key]
    return "latest"


def seed_all(db: Session, client: OpenF1Client, season: int) -> dict:
    """Seed constructors, drivers, races, and the default league for a season."""
    races_data = client.fetch_races(season)
    races = seed_races(db, races_data, season)

    session_key = _representative_session_key(races_data)
    drivers_data = client.fetch_drivers(session_key)

    constructors = seed_constructors(db, drivers_data, season)
    drivers = seed_drivers(db, drivers_data, season, constructors)
    league = seed_default_league(db)

    db.commit()
    return {
        "constructors": len(constructors),
        "drivers": len(drivers),
        "races": len(races),
        "league": league.name,
    }
