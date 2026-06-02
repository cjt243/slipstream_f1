"""SQLAlchemy declarative base. All ORM models inherit from Base."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for every model in the project."""

    pass
