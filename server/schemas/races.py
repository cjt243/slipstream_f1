"""Race calendar schemas (see docs/api-contracts.md#get-races)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_serializer

RaceStatus = Literal["upcoming", "lockdown", "completed"]


class RaceResponse(BaseModel):
    id: int
    season: int
    round: int
    name: str
    circuit: str | None
    total_laps: int | None
    has_sprint: bool
    lockdown_at: datetime | None
    race_start_at: datetime | None
    status: RaceStatus

    # DB datetimes are naive UTC; serialise with an explicit Z.
    @field_serializer("lockdown_at", "race_start_at")
    def as_utc(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%dT%H:%M:%SZ") if value else None


class RaceListResponse(BaseModel):
    next_race: int | None
    races: list[RaceResponse]


class RaceDetailResponse(RaceResponse):
    lockdown_active: bool
    results_available: bool
