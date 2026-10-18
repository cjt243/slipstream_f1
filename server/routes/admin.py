"""Admin-only operations (seeding, results ingestion, salary adjustment)."""

from fastapi import APIRouter, HTTPException, status

from config import settings
from dependencies import AdminUser, DbSession, OpenF1
from models import Race
from schemas.admin import (
    RaceRequest,
    ResultsResponse,
    SalaryAdjustResponse,
    SeedRequest,
    SeedResponse,
)
from services import races as race_service
from services.results import process_race_results
from services.salary import adjust_salaries
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
    """Ingest a race's results from OpenF1 and score it. Safe to re-run."""
    race = _race_or_404(db, body.race_id)
    processed = process_race_results(db, openf1, race)
    if processed is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="OpenF1 has no results for this race yet"
        )
    return ResultsResponse(
        race_id=processed.race_id,
        drivers_scored=processed.drivers_scored,
        constructors_scored=processed.constructors_scored,
    )


@router.post("/salary-adjust", response_model=SalaryAdjustResponse)
def salary_adjust(body: RaceRequest, _: AdminUser, db: DbSession) -> SalaryAdjustResponse:
    """Apply a scored race's salary adjustments (once per race, in round order)."""
    race = _race_or_404(db, body.race_id)
    try:
        count = adjust_salaries(db, race)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return SalaryAdjustResponse(race_id=race.id, adjustments=count)
