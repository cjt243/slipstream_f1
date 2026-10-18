"""Post-race pipeline shared by the admin API, the CLI and the scheduled job.

1. ``process_race_results`` (services/results.py): ingest, score drivers and
   constructors, score fantasy teams.
2. ``finalize_race``: adjust salaries, settle contracts that ended at this
   race at their post-race salary, apply the £100M team-value floor.

``process_due_races`` runs both for every race whose results should be out.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import Race
from services import races as race_service
from services.contracts import settle_expired_contracts
from services.fantasy import apply_team_value_floor
from services.openf1 import OpenF1Client
from services.results import process_race_results
from services.salary import adjust_salaries, is_adjusted

# Results are fetched once the race should be over and classified (a GP is
# ~2h; this leaves time for immediate stewards' decisions).
RESULTS_DELAY = timedelta(hours=4)


def finalize_race(db: Session, race: Race) -> int:
    """Salary adjustment + contract settlement + team-value floor for a scored
    race. Returns the number of salary adjustments. Raises ValueError (see
    ``adjust_salaries``) if the race can't be finalized yet or already was.
    Does not commit."""
    count = adjust_salaries(db, race)
    settle_expired_contracts(db, race)
    next_race = race_service.current_race(db, race.season)
    apply_team_value_floor(db, next_race.round if next_race else None)
    return count


def process_due_races(db: Session, client: OpenF1Client, season: int, now: datetime) -> list[str]:
    """Process and finalize, in round order, every race that started at least
    RESULTS_DELAY ago and isn't finalized yet. Stops at the first race that
    isn't due or whose results aren't out. Returns a log line per step."""
    log: list[str] = []
    for race in race_service.list_races(db, season):
        if is_adjusted(db, race):
            continue
        if race.race_start_at is None or race.race_start_at + RESULTS_DELAY > now:
            log.append(f"R{race.round} {race.name}: not due yet")
            break
        processed = process_race_results(db, client, race)
        if processed is None:
            log.append(f"R{race.round} {race.name}: no results from OpenF1 yet")
            break
        count = finalize_race(db, race)
        db.commit()
        log.append(f"R{race.round} {race.name}: {processed.drivers_scored} drivers scored, "
                   f"{count} salaries adjusted")
    return log
