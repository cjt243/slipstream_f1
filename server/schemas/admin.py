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
