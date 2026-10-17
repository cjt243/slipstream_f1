from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DriverResult(Base):
    __tablename__ = "driver_results"
    __table_args__ = (UniqueConstraint("race_id", "driver_id", name="uq_driver_result"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quali_pos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sprint_pos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    race_pos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    laps_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dnf: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ConstructorResult(Base):
    __tablename__ = "constructor_results"
    __table_args__ = (
        UniqueConstraint("race_id", "constructor_id", name="uq_constructor_result"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False
    )
    constructor_id: Mapped[int] = mapped_column(
        ForeignKey("constructors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quali_pos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    race_pos: Mapped[int | None] = mapped_column(Integer, nullable=True)
