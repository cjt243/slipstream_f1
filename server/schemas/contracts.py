"""Contract schemas (see docs/api-contracts.md#contracts)."""

from datetime import datetime

from pydantic import BaseModel, field_serializer

from models import ElementType


class ContractCreate(BaseModel):
    element_type: ElementType
    element_id: int
    contract_length: int  # 1–5, validated by the service (400, not 422)


class ContractResponse(BaseModel):
    id: int
    element_type: ElementType
    element_id: int
    element_name: str
    element_color: str | None
    constructor_name: str | None  # drivers only
    signed_salary: int
    current_salary: int
    race_start: int
    contract_length: int
    last_round: int
    races_remaining: int
    # True until the first race locks: releasing is then a free cancellation.
    cancellable: bool


class CurrentRace(BaseModel):
    id: int
    round: int
    name: str
    lockdown_at: datetime | None
    locked: bool
    races_left: int

    @field_serializer("lockdown_at")
    def as_utc(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%dT%H:%M:%SZ") if value else None


class CooldownElement(BaseModel):
    element_type: ElementType
    element_id: int


class ContractListResponse(BaseModel):
    contracts: list[ContractResponse]
    bank_balance: int
    contract_value: int
    team_value: int
    current_race: CurrentRace | None
    cooldown: list[CooldownElement]
    star_driver_id: int | None  # the current race's star pick
    star_max_salary: int  # star drivers must earn less than this


class ReleaseResponse(BaseModel):
    released: bool
    penalty: int
    refund: int
    bank_balance: int


class StarRequest(BaseModel):
    driver_id: int


class StarResponse(BaseModel):
    star_driver_id: int | None
