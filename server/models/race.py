from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Race(Base):
    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("season", "round", name="uq_race_season_round"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    circuit: Mapped[str | None] = mapped_column(String, nullable=True)
    total_laps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_sprint: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lockdown_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # OpenF1 identifiers used by the ingestion service (issue 1B).
    meeting_key: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quali_session_key: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sprint_session_key: Mapped[int | None] = mapped_column(Integer, nullable=True)
    race_session_key: Mapped[int | None] = mapped_column(Integer, nullable=True)
