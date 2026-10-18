"""Current-season driver and constructor reference data (public)."""

from fastapi import APIRouter

from config import settings
from dependencies import DbSession
from models import Driver
from schemas.roster import (
    ConstructorListResponse,
    ConstructorResponse,
    DriverListResponse,
    DriverResponse,
)
from services import roster as roster_service

router = APIRouter(tags=["roster"])


def driver_response(driver: Driver) -> DriverResponse:
    return DriverResponse(
        id=driver.id,
        name=driver.name,
        code=driver.code,
        driver_number=driver.driver_number,
        constructor_id=driver.constructor_id,
        constructor_name=driver.constructor.name,
        constructor_color=driver.constructor.color,
        salary=driver.salary,
        season=driver.season,
    )


@router.get("/drivers", response_model=DriverListResponse)
def list_drivers(db: DbSession) -> DriverListResponse:
    drivers = roster_service.list_drivers(db, settings.season)
    return DriverListResponse(drivers=[driver_response(d) for d in drivers])


@router.get("/constructors", response_model=ConstructorListResponse)
def list_constructors(db: DbSession) -> ConstructorListResponse:
    constructors = roster_service.list_constructors(db, settings.season)
    return ConstructorListResponse(
        constructors=[ConstructorResponse.model_validate(c) for c in constructors]
    )
