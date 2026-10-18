"""Admin-only operations (seeding, results ingestion, salary adjustment)."""

from fastapi import APIRouter

from config import settings
from dependencies import AdminUser, DbSession, OpenF1
from schemas.admin import SeedRequest, SeedResponse
from services.seed import seed_all

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed", response_model=SeedResponse)
def seed(body: SeedRequest, _: AdminUser, db: DbSession, openf1: OpenF1) -> SeedResponse:
    """Seed (or refresh) a season's races, constructors and drivers. Idempotent."""
    season = body.season or settings.season
    result = seed_all(db, openf1, season)
    return SeedResponse(season=season, **result)
