"""Per-race scoring breakdowns (public)."""

from fastapi import APIRouter, HTTPException, status

from dependencies import DbSession
from schemas.scores import (
    ConstructorScoreResponse,
    ConstructorScoresResponse,
    DriverScoreResponse,
    DriverScoresResponse,
)
from services import races as race_service
from services import results as results_service

router = APIRouter(prefix="/scores", tags=["scores"])


def _require_race(db: DbSession, race_id: int) -> None:
    if race_service.get_race(db, race_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")


def _not_scored() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Results not available yet")


@router.get("/{race_id}/drivers", response_model=DriverScoresResponse)
def driver_scores(race_id: int, db: DbSession) -> DriverScoresResponse:
    _require_race(db, race_id)
    rows = results_service.get_driver_scores(db, race_id)
    if not rows:
        raise _not_scored()
    return DriverScoresResponse(
        race_id=race_id,
        scores=[
            DriverScoreResponse(
                driver_id=driver.id,
                driver_name=driver.name,
                code=driver.code,
                constructor_name=team.name if team else None,
                constructor_color=team.color if team else None,
                quali_pos=result.quali_pos if result else None,
                sprint_pos=result.sprint_pos if result else None,
                race_pos=result.race_pos if result else None,
                dnf=result.dnf if result else False,
                quali_pts=score.quali_pts,
                race_pts=score.race_pts,
                sprint_pts=score.sprint_pts,
                overtake_pts=score.overtake_pts,
                improvement_pts=score.improvement_pts,
                teammate_pts=score.teammate_pts,
                completion_pts=score.completion_pts,
                total_pts=score.total_pts,
            )
            for score, driver, result, team in rows
        ],
    )


@router.get("/{race_id}/constructors", response_model=ConstructorScoresResponse)
def constructor_scores(race_id: int, db: DbSession) -> ConstructorScoresResponse:
    _require_race(db, race_id)
    rows = results_service.get_constructor_scores(db, race_id)
    if not rows:
        raise _not_scored()
    return ConstructorScoresResponse(
        race_id=race_id,
        scores=[
            ConstructorScoreResponse(
                constructor_id=team.id,
                constructor_name=team.name,
                constructor_color=team.color,
                quali_rank=result.quali_pos if result else None,
                race_rank=result.race_pos if result else None,
                quali_pts=score.quali_pts,
                race_pts=score.race_pts,
                total_pts=score.total_pts,
            )
            for score, team, result in rows
        ],
    )
