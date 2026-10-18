"""Race results: ingest from OpenF1, then score drivers and constructors.

``ingest_race_results`` stores positions in driver_results/constructor_results;
``score_race`` turns them into driver_scores/constructor_scores using the pure
rules in ``services/scoring.py``. Both upsert, so re-running a race is safe
(e.g. after a post-race penalty changes the classification).
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from models import (
    Constructor,
    ConstructorResult,
    ConstructorScore,
    Driver,
    DriverResult,
    DriverScore,
    Race,
)
from services import scoring
from services.openf1 import OpenF1Client
from services.seed import seed_constructors, upsert_driver


@dataclass(frozen=True)
class SessionPlace:
    position: int
    laps: int
    dnf: bool


def normalize_session(rows: list[dict]) -> dict[int, SessionPlace]:
    """Turn an OpenF1 session_result into a full 1..n order, keyed by driver
    number. Classified drivers keep their order; unclassified ones (position
    null or a code like "RT") follow, most laps first; DSQ and DNS go last."""

    def numeric(row: dict) -> int | None:
        pos = row.get("position")
        return pos if isinstance(pos, int) else None

    def sort_key(row: dict) -> tuple:
        pos = numeric(row)
        laps = row.get("number_of_laps") or 0
        if row.get("dsq") or row.get("dns"):
            return (2, -laps)
        if pos is not None:
            return (0, pos)
        return (1, -laps)

    rows = [r for r in rows if r.get("driver_number") is not None]
    ordered = sorted(rows, key=sort_key)
    return {
        r["driver_number"]: SessionPlace(
            position=i,
            laps=r.get("number_of_laps") or 0,
            dnf=bool(r.get("dnf") or r.get("dns") or r.get("dsq")),
        )
        for i, r in enumerate(ordered, start=1)
    }


def ingest_race_results(db: Session, client: OpenF1Client, race: Race) -> int | None:
    """Fetch and store a race weekend's results. Returns the number of drivers
    stored, or None if OpenF1 has no race results yet."""
    if race.race_session_key is None:
        return None
    race_rows = client.fetch_session_result(race.race_session_key)
    if not race_rows:
        return None
    quali = normalize_session(
        client.fetch_session_result(race.quali_session_key) if race.quali_session_key else []
    )
    sprint = normalize_session(
        client.fetch_session_result(race.sprint_session_key)
        if race.has_sprint and race.sprint_session_key else []
    )
    finish = normalize_session(race_rows)

    # The race session's entry list gives each driver's team *at this race*;
    # unknown numbers (stand-in drivers) are created at their starting salary.
    entries = client.fetch_drivers(race.race_session_key)
    constructors = seed_constructors(db, entries, race.season)
    team_by_number = {e["driver_number"]: constructors[e["team_name"]].id
                      for e in entries if e.get("team_name") in constructors}
    drivers = {d.driver_number: d for d in db.query(Driver).filter_by(season=race.season)}
    for e in entries:
        if e["driver_number"] not in drivers:
            created = upsert_driver(db, e, race.season, constructors)
            if created is not None:
                drivers[e["driver_number"]] = created
    db.flush()

    existing = {r.driver_id: r for r in db.query(DriverResult).filter_by(race_id=race.id)}
    stored = 0
    for number, place in finish.items():
        driver = drivers.get(number)
        if driver is None:
            continue
        row = existing.get(driver.id) or DriverResult(race_id=race.id, driver_id=driver.id)
        row.constructor_id = team_by_number.get(number, driver.constructor_id)
        row.quali_pos = quali[number].position if number in quali else None
        row.sprint_pos = sprint[number].position if number in sprint else None
        row.race_pos = place.position
        row.laps_completed = place.laps
        row.dnf = place.dnf
        db.add(row)
        stored += 1

    # Race distance = the winner's lap count.
    winner = next((p for p in finish.values() if p.position == 1), None)
    race.total_laps = winner.laps if winner else race.total_laps
    db.flush()
    _store_constructor_results(db, race)
    return stored


def _store_constructor_results(db: Session, race: Race) -> None:
    results = db.query(DriverResult).filter_by(race_id=race.id).all()
    quali: dict[int, list[int]] = {}
    finish: dict[int, list[int]] = {}
    for r in results:
        if r.constructor_id is None:
            continue
        if r.quali_pos:
            quali.setdefault(r.constructor_id, []).append(r.quali_pos)
        if r.race_pos:
            finish.setdefault(r.constructor_id, []).append(r.race_pos)
    quali_rank = scoring.rank_constructors(quali)
    race_rank = scoring.rank_constructors(finish)

    existing = {c.constructor_id: c for c in db.query(ConstructorResult).filter_by(race_id=race.id)}
    for cid in set(quali) | set(finish):
        row = existing.get(cid) or ConstructorResult(race_id=race.id, constructor_id=cid)
        row.quali_pos = quali_rank.get(cid)
        row.race_pos = race_rank.get(cid)
        db.add(row)
    db.flush()


def _previous_finishes(db: Session, race: Race) -> dict[int, list[int]]:
    """Each driver's race finishes this season before ``race``, oldest first."""
    rows = (
        db.query(DriverResult.driver_id, DriverResult.race_pos)
        .join(Race, Race.id == DriverResult.race_id)
        .filter(Race.season == race.season, Race.round < race.round,
                DriverResult.race_pos.is_not(None))
        .order_by(Race.round)
        .all()
    )
    history: dict[int, list[int]] = {}
    for driver_id, pos in rows:
        history.setdefault(driver_id, []).append(pos)
    return history


def score_race(db: Session, race: Race) -> tuple[int, int]:
    """(Re)compute driver and constructor scores from stored results.
    Returns (drivers_scored, constructors_scored)."""
    results = db.query(DriverResult).filter_by(race_id=race.id).all()
    history = _previous_finishes(db, race)
    inputs = [
        scoring.DriverRaceInput(
            driver_id=r.driver_id, constructor_id=r.constructor_id, quali_pos=r.quali_pos,
            sprint_pos=r.sprint_pos, race_pos=r.race_pos, laps_completed=r.laps_completed,
        )
        for r in results
    ]
    points = scoring.score_drivers(
        inputs,
        total_laps=race.total_laps,
        has_sprint=race.has_sprint,
        rolling_averages={r.driver_id: scoring.rolling_average(history.get(r.driver_id, []))
                          for r in results},
    )
    existing = {s.driver_id: s for s in db.query(DriverScore).filter_by(race_id=race.id)}
    for driver_id, p in points.items():
        row = existing.get(driver_id) or DriverScore(race_id=race.id, driver_id=driver_id)
        row.quali_pts, row.sprint_pts, row.race_pts = p.quali_pts, p.sprint_pts, p.race_pts
        row.overtake_pts, row.improvement_pts = p.overtake_pts, p.improvement_pts
        row.teammate_pts, row.completion_pts = p.teammate_pts, p.completion_pts
        row.total_pts = p.total_pts
        db.add(row)

    team_results = db.query(ConstructorResult).filter_by(race_id=race.id).all()
    existing_c = {s.constructor_id: s for s in db.query(ConstructorScore).filter_by(race_id=race.id)}
    for tr in team_results:
        row = existing_c.get(tr.constructor_id) or ConstructorScore(
            race_id=race.id, constructor_id=tr.constructor_id
        )
        row.quali_pts = scoring.constructor_quali_points(tr.quali_pos)
        row.race_pts = scoring.constructor_race_points(tr.race_pos)
        row.total_pts = row.quali_pts + row.race_pts
        db.add(row)
    db.flush()
    return len(points), len(team_results)


@dataclass(frozen=True)
class ProcessedRace:
    race_id: int
    drivers_scored: int
    constructors_scored: int


def process_race_results(db: Session, client: OpenF1Client, race: Race) -> ProcessedRace | None:
    """Ingest + score one race and commit. None if results aren't out yet."""
    if ingest_race_results(db, client, race) is None:
        return None
    drivers, constructors = score_race(db, race)
    db.commit()
    return ProcessedRace(race.id, drivers, constructors)


def get_driver_scores(
    db: Session, race_id: int
) -> list[tuple[DriverScore, Driver, DriverResult | None, Constructor | None]]:
    """A race's driver scores with the driver, their result and the team they
    raced for, highest total first."""
    return (
        db.query(DriverScore, Driver, DriverResult, Constructor)
        .join(Driver, Driver.id == DriverScore.driver_id)
        .outerjoin(DriverResult, (DriverResult.race_id == DriverScore.race_id)
                   & (DriverResult.driver_id == DriverScore.driver_id))
        .outerjoin(Constructor, Constructor.id == DriverResult.constructor_id)
        .filter(DriverScore.race_id == race_id)
        .order_by(DriverScore.total_pts.desc(), Driver.name)
        .all()
    )


def get_constructor_scores(
    db: Session, race_id: int
) -> list[tuple[ConstructorScore, Constructor, ConstructorResult | None]]:
    """A race's constructor scores with the team and its ranks, highest total first."""
    return (
        db.query(ConstructorScore, Constructor, ConstructorResult)
        .join(Constructor, Constructor.id == ConstructorScore.constructor_id)
        .outerjoin(ConstructorResult, (ConstructorResult.race_id == ConstructorScore.race_id)
                   & (ConstructorResult.constructor_id == ConstructorScore.constructor_id))
        .filter(ConstructorScore.race_id == race_id)
        .order_by(ConstructorScore.total_pts.desc(), Constructor.name)
        .all()
    )
