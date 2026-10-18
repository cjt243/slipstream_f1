"""Season race calendar (public)."""

from fastapi import APIRouter, HTTPException, status

from config import settings
from dependencies import DbSession
from models import Race
from schemas.races import RaceDetailResponse, RaceListResponse, RaceResponse
from services import races as race_service

router = APIRouter(prefix="/races", tags=["races"])


@router.get("", response_model=RaceListResponse)
def list_races(db: DbSession) -> RaceListResponse:
    races = race_service.list_races(db, settings.season)
    with_results = race_service.races_with_results(db, [r.id for r in races])
    now = race_service.utcnow()
    nxt = race_service.next_race(races, with_results)
    return RaceListResponse(
        next_race=nxt.id if nxt else None,
        races=[
            RaceResponse(
                **_fields(r), status=race_service.race_status(r, r.id in with_results, now)
            )
            for r in races
        ],
    )


@router.get("/{race_id}", response_model=RaceDetailResponse)
def get_race(race_id: int, db: DbSession) -> RaceDetailResponse:
    race = race_service.get_race(db, race_id)
    if race is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
    has_results = race.id in race_service.races_with_results(db, [race.id])
    race_status = race_service.race_status(race, has_results, race_service.utcnow())
    return RaceDetailResponse(
        **_fields(race),
        status=race_status,
        lockdown_active=race_status == race_service.LOCKDOWN,
        results_available=has_results,
    )


def _fields(race: Race) -> dict:
    return {
        "id": race.id,
        "season": race.season,
        "round": race.round,
        "name": race.name,
        "circuit": race.circuit,
        "total_laps": race.total_laps,
        "has_sprint": race.has_sprint,
        "lockdown_at": race.lockdown_at,
        "race_start_at": race.race_start_at,
    }
