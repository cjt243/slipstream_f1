"""Initial season seeding from OpenF1 + static salary data.

Idempotent: every function checks for an existing row by its natural key before
inserting, and never truncates. Re-running ``seed_all`` is safe — it fills gaps
and refreshes race scheduling fields without clobbering salaries that may have
since been adjusted by the scoring engine.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from data.salaries_2025 import starting_constructor_salary, starting_driver_salary
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
    seen: set[str] = set()
    for d in drivers_data:
        team = d.get("team_name")
        if not team or team in seen:
            continue
        seen.add(team)
        if team in existing:
            continue
        c = Constructor(
            name=team,
            color=d.get("team_color"),
            salary=starting_constructor_salary(team),
            season=season,
        )
        db.add(c)
        existing[team] = c
    db.flush()
    return existing


def seed_drivers(
    db: Session, drivers_data: list[dict], season: int, constructors: dict[str, Constructor]
) -> list[Driver]:
    existing = {d.driver_number: d for d in db.query(Driver).filter_by(season=season)}
    created: list[Driver] = []
    for d in drivers_data:
        num = d.get("driver_number")
        team = d.get("team_name")
        if num is None or num in existing or team not in constructors:
            continue
        driver = Driver(
            name=d.get("name"),
            driver_number=num,
            code=d.get("code"),
            constructor_id=constructors[team].id,
            salary=starting_driver_salary(num),
            season=season,
        )
        db.add(driver)
        existing[num] = driver
        created.append(driver)
    db.flush()
    return created


def seed_races(db: Session, races_data: list[dict], season: int) -> list[Race]:
    existing = {r.round: r for r in db.query(Race).filter_by(season=season)}
    result: list[Race] = []
    for rd in races_data:
        rnd = rd["round"]
        race = existing.get(rnd)
        if race is None:
            race = Race(season=season, round=rnd)
            db.add(race)
        # Scheduling/identifier fields are safe to refresh on re-seed.
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


def _representative_session_key(races_data: list[dict]) -> int | str:
    """A session_key from this season so the driver feed matches the season
    (using 'latest' would return whatever session is most recent overall)."""
    for rd in races_data:
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
