"""Leaderboard schemas (see docs/api-contracts.md#leaderboard)."""

from pydantic import BaseModel


class StandingEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    total_points: int
    team_value: int
    bank_balance: int
    is_current_user: bool


class ScoredRace(BaseModel):
    id: int
    round: int
    name: str


class LeaderboardResponse(BaseModel):
    standings: list[StandingEntry]
    races: list[ScoredRace]  # races with fantasy points, for the per-race view


class RaceStandingEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    race_points: int
    is_current_user: bool


class RaceLeaderboardResponse(BaseModel):
    race_id: int
    standings: list[RaceStandingEntry]
