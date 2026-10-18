"""League standings — season and per race (public; flags the viewer's row)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from config import settings
from dependencies import DbSession, get_optional_user
from models import League, User
from schemas.leaderboard import (
    LeaderboardResponse,
    RaceLeaderboardResponse,
    RaceStandingEntry,
    ScoredRace,
    StandingEntry,
)
from services import fantasy
from services import races as race_service
from services.seed import seed_default_league

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def _league(db: DbSession) -> League:
    return seed_default_league(db)


@router.get("", response_model=LeaderboardResponse)
def season(db: DbSession, viewer: OptionalUser) -> LeaderboardResponse:
    league = _league(db)
    current = race_service.current_race(db, settings.season)
    current_round = current.round if current else None
    standings = fantasy.season_standings(db, league.id, settings.season)
    return LeaderboardResponse(
        standings=[
            StandingEntry(
                rank=s.rank,
                user_id=s.user.id,
                username=s.user.username,
                total_points=s.points,
                team_value=fantasy.team_value(db, s.member, current_round),
                bank_balance=s.member.bank_balance,
                is_current_user=viewer is not None and viewer.id == s.user.id,
            )
            for s in standings
        ],
        races=[ScoredRace(id=r.id, round=r.round, name=r.name)
               for r in fantasy.scored_races(db, league.id, settings.season)],
    )


@router.get("/{race_id}", response_model=RaceLeaderboardResponse)
def for_race(race_id: int, db: DbSession, viewer: OptionalUser) -> RaceLeaderboardResponse:
    if race_service.get_race(db, race_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
    league = _league(db)
    return RaceLeaderboardResponse(
        race_id=race_id,
        standings=[
            RaceStandingEntry(
                rank=s.rank,
                user_id=s.user.id,
                username=s.user.username,
                race_points=s.points,
                is_current_user=viewer is not None and viewer.id == s.user.id,
            )
            for s in fantasy.race_standings(db, league.id, race_id)
        ],
    )
