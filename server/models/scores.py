from sqlalchemy import BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DriverScore(Base):
    __tablename__ = "driver_scores"
    __table_args__ = (UniqueConstraint("race_id", "driver_id", name="uq_driver_score"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False
    )
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quali_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sprint_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    race_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overtake_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    improvement_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    teammate_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ConstructorScore(Base):
    __tablename__ = "constructor_scores"
    __table_args__ = (
        UniqueConstraint("race_id", "constructor_id", name="uq_constructor_score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False
    )
    constructor_id: Mapped[int] = mapped_column(
        ForeignKey("constructors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quali_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    race_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class FantasyScore(Base):
    """A user's total fantasy points for one race in one league."""

    __tablename__ = "fantasy_scores"
    __table_args__ = (
        UniqueConstraint("user_id", "league_id", "race_id", name="uq_fantasy_score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False
    )
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
