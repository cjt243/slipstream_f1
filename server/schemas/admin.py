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


class RemindersResponse(BaseModel):
    race_id: int | None
    race_name: str | None
    due: bool  # lockdown is within the reminder window
    sent: list[str]  # usernames emailed by this call
    logged: list[str]  # usernames whose email was only logged: no RESEND_API_KEY (not recorded)
    failed: list[str]  # usernames whose email failed (retried on the next run)
