"""Driver and constructor reference data for a season."""

from sqlalchemy.orm import Session, joinedload

from models import Constructor, Driver


def list_drivers(db: Session, season: int) -> list[Driver]:
    """All drivers in a season (constructor eagerly loaded), by number."""
    return (
        db.query(Driver)
        .options(joinedload(Driver.constructor))
        .filter(Driver.season == season)
        .order_by(Driver.driver_number)
        .all()
    )


def list_constructors(db: Session, season: int) -> list[Constructor]:
    """All constructors in a season, by name."""
    return (
        db.query(Constructor)
        .filter(Constructor.season == season)
        .order_by(Constructor.name)
        .all()
    )
