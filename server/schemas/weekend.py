"""Race weekend view schemas (see docs/api-contracts.md#get-weekendrace_id)."""

from pydantic import BaseModel

from models import ElementType
from schemas.races import RaceDetailResponse


class LineupElementResponse(BaseModel):
    element_type: ElementType
    element_id: int
    name: str
    code: str | None
    color: str | None
    constructor_name: str | None
    points: int | None
    quali_pos: int | None
    race_pos: int | None


class LineupResponse(BaseModel):
    user_id: int
    username: str
    is_current_user: bool
    rank: int | None
    points: int | None
    elements: list[LineupElementResponse]


class QualiEntryResponse(BaseModel):
    driver_id: int
    driver_name: str
    code: str | None
    constructor_name: str | None
    constructor_color: str | None
    quali_pos: int
    quali_pts: int | None
    picked_by: int | None


class WeekendResponse(BaseModel):
    race: RaceDetailResponse
    locked: bool
    scored: bool
    winners: list[LineupResponse]
    lineups: list[LineupResponse]
    hidden_lineups: int
    qualifying: list[QualiEntryResponse]
