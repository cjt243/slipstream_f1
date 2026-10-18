"""Current-season driver and constructor reference data (public)."""

from fastapi import APIRouter

from config import settings
from dependencies import DbSession
from models import Driver, ElementType
from schemas.roster import (
    ConstructorListResponse,
    ConstructorResponse,
    DriverListResponse,
    DriverResponse,
)
from services import roster as roster_service
from services.salary import latest_changes

router = APIRouter(tags=["roster"])


def driver_response(driver: Driver, salary_change: int | None = None) -> DriverResponse:
    return DriverResponse(
        id=driver.id,
        name=driver.name,
        code=driver.code,
        driver_number=driver.driver_number,
        constructor_id=driver.constructor_id,
        constructor_name=driver.constructor.name,
        constructor_color=driver.constructor.color,
        salary=driver.salary,
        salary_change=salary_change,
        season=driver.season,
    )


@router.get("/drivers", response_model=DriverListResponse)
def list_drivers(db: DbSession) -> DriverListResponse:
    drivers = roster_service.list_drivers(db, settings.season)
    changes = latest_changes(db, ElementType.DRIVER)
    return DriverListResponse(drivers=[driver_response(d, changes.get(d.id)) for d in drivers])


@router.get("/constructors", response_model=ConstructorListResponse)
def list_constructors(db: DbSession) -> ConstructorListResponse:
    constructors = roster_service.list_constructors(db, settings.season)
    changes = latest_changes(db, ElementType.CONSTRUCTOR)
    return ConstructorListResponse(
        constructors=[
            ConstructorResponse.model_validate(c).model_copy(update={"salary_change": changes.get(c.id)})
            for c in constructors
        ]
    )
