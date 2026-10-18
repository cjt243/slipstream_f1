"""Race weekend view: lineups, winner and qualifying for one race (public;
lineups other than the viewer's appear at lockdown)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import DbSession, get_optional_user
from models import User
from routes.races import race_detail
from schemas.weekend import (
    LineupElementResponse,
    LineupResponse,
    MoveResponse,
    MovesResponse,
    QualiEntryResponse,
    WeekendResponse,
)
from services import races as race_service
from services.race_weekend import Lineup, race_weekend
from services.seed import seed_default_league

router = APIRouter(prefix="/weekend", tags=["weekend"])
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def _lineup(lu: Lineup, viewer: User | None) -> LineupResponse:
    return LineupResponse(
        user_id=lu.user.id,
        username=lu.user.username,
        is_current_user=viewer is not None and lu.user.id == viewer.id,
        rank=lu.rank,
        points=lu.points,
        floor_applied=lu.floor_applied,
        elements=[LineupElementResponse(**e.__dict__) for e in lu.elements],
        moves=MovesResponse(
            signed=[MoveResponse(**m.__dict__) for m in lu.moves.signed],
            dropped=[MoveResponse(**m.__dict__) for m in lu.moves.dropped],
            kept=lu.moves.kept,
        ),
    )


@router.get("/{race_id}", response_model=WeekendResponse)
def weekend(race_id: int, db: DbSession, viewer: OptionalUser) -> WeekendResponse:
    race = race_service.get_race(db, race_id)
    if race is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
    w = race_weekend(db, race, seed_default_league(db).id, viewer, race_service.utcnow())
    return WeekendResponse(
        race=race_detail(db, race),
        locked=w.locked,
        scored=w.scored,
        final=w.final,
        winners=[_lineup(lu, viewer) for lu in w.winners],
        lineups=[_lineup(lu, viewer) for lu in w.lineups],
        hidden_lineups=w.hidden,
        qualifying=[
            QualiEntryResponse(
                driver_id=q.driver.id,
                driver_name=q.driver.name,
                code=q.driver.code,
                constructor_name=q.team.name if q.team else None,
                constructor_color=q.team.color if q.team else None,
                quali_pos=q.quali_pos,
                quali_pts=q.quali_pts,
                picked_by=q.picked_by,
            )
            for q in w.qualifying
        ],
    )
