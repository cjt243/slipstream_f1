"""Admin request/response schemas (see docs/api-contracts.md#admin)."""

from pydantic import BaseModel, Field


class SeedRequest(BaseModel):
    season: int | None = Field(default=None, ge=2023, le=2100)


class SeedResponse(BaseModel):
    season: int
    constructors: int
    drivers: int
    races: int
    league: str


class RaceRequest(BaseModel):
    race_id: int


class ResultsResponse(BaseModel):
    race_id: int
    drivers_scored: int
    constructors_scored: int


class SalaryAdjustResponse(BaseModel):
    race_id: int
    adjustments: int
