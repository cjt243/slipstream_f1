"""Per-race scoring breakdown schemas (see docs/api-contracts.md#scores)."""

from pydantic import BaseModel


class DriverScoreResponse(BaseModel):
    driver_id: int
    driver_name: str
    code: str | None
    constructor_name: str | None
    constructor_color: str | None
    quali_pos: int | None
    sprint_pos: int | None
    race_pos: int | None
    dnf: bool
    quali_pts: int
    race_pts: int
    sprint_pts: int
    overtake_pts: int
    improvement_pts: int
    teammate_pts: int
    completion_pts: int
    total_pts: int


class DriverScoresResponse(BaseModel):
    race_id: int
    scores: list[DriverScoreResponse]


class ConstructorScoreResponse(BaseModel):
    constructor_id: int
    constructor_name: str
    constructor_color: str | None
    quali_rank: int | None
    race_rank: int | None
    quali_pts: int
    race_pts: int
    total_pts: int


class ConstructorScoresResponse(BaseModel):
    race_id: int
    scores: list[ConstructorScoreResponse]
