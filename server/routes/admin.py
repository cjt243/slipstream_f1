"""Admin-only operations (seeding, results ingestion, salary adjustment,
lineup reminders)."""

from fastapi import APIRouter, HTTPException, status

from config import settings
from dependencies import AdminUser, DbSession, OpenF1
from models import Race
from schemas.admin import (
    RaceRequest,
    RemindersResponse,
    ResultsResponse,
    SalaryAdjustResponse,
    SeedRequest,
    SeedResponse,
)
from services import races as race_service
from services.notifications import reminder_due, send_lineup_reminders
from services.results import process_early_sessions, process_race_results
from services.weekend import finalize_race
from services.seed import seed_all

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed", response_model=SeedResponse)
def seed(body: SeedRequest, _: AdminUser, db: DbSession, openf1: OpenF1) -> SeedResponse:
    """Seed (or refresh) a season's races, constructors and drivers. Idempotent."""
    season = body.season or settings.season
    result = seed_all(db, openf1, season)
    return SeedResponse(season=season, **result)


def _race_or_404(db: DbSession, race_id: int) -> Race:
    race = race_service.get_race(db, race_id)
    if race is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
    return race


@router.post("/results", response_model=ResultsResponse)
def ingest_results(
    body: RaceRequest, _: AdminUser, db: DbSession, openf1: OpenF1
) -> ResultsResponse:
    """Ingest a race's results from OpenF1 and score it. Safe to re-run.
    Before the race result is out, scores qualifying/sprint live instead."""
    race = _race_or_404(db, body.race_id)
    processed = process_race_results(db, openf1, race)
    live = processed is None
    if live:
        processed = process_early_sessions(db, openf1, race)
    if processed is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="OpenF1 has no results for this race yet"
        )
    return ResultsResponse(
        race_id=processed.race_id,
        drivers_scored=processed.drivers_scored,
        constructors_scored=processed.constructors_scored,
        live=live,
    )


@router.post("/salary-adjust", response_model=SalaryAdjustResponse)
def salary_adjust(body: RaceRequest, _: AdminUser, db: DbSession) -> SalaryAdjustResponse:
    """Apply a scored race's salary adjustments (once per race, in round order),
    settle contracts that ended at this race and apply the team-value floor."""
    race = _race_or_404(db, body.race_id)
    try:
        count = finalize_race(db, race)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return SalaryAdjustResponse(race_id=race.id, adjustments=count)


@router.post("/reminders", response_model=RemindersResponse)
def reminders(_: AdminUser, db: DbSession) -> RemindersResponse:
    """Email members with an incomplete team for the current race, if its
    lockdown is within 24h. Each member is reminded once per race."""
    now = race_service.utcnow()
    run = send_lineup_reminders(db, settings.season, now)
    return RemindersResponse(
        race_id=run.race.id if run.race else None,
        race_name=run.race.name if run.race else None,
        due=reminder_due(run.race, now),
        sent=run.sent,
        logged=run.logged,
        failed=run.failed,
    )
