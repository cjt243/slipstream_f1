"""Driver/constructor reference-data schemas (see docs/api-contracts.md#reference-data)."""

from pydantic import BaseModel, ConfigDict


class DriverResponse(BaseModel):
    id: int
    name: str
    code: str | None
    driver_number: int
    constructor_id: int
    constructor_name: str
    constructor_color: str | None
    salary: int
    season: int


class DriverListResponse(BaseModel):
    drivers: list[DriverResponse]


class ConstructorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str | None
    salary: int
    season: int


class ConstructorListResponse(BaseModel):
    constructors: list[ConstructorResponse]
