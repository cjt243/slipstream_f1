"""Post-race pipeline shared by the admin API, the CLI and the scheduled job.

1. ``process_race_results`` (services/results.py): ingest, score drivers and
   constructors, score fantasy teams.
2. ``finalize_race``: adjust salaries, settle contracts that ended at this
   race at their post-race salary, apply the £100M team-value floor.
"""

from sqlalchemy.orm import Session

from models import Race
from services import races as race_service
from services.contracts import settle_expired_contracts
from services.fantasy import apply_team_value_floor
from services.salary import adjust_salaries


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
