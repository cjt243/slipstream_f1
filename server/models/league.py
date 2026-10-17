from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

# £100,000,000 starting budget, stored in whole pounds.
STARTING_BUDGET = 100_000_000


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    invite_code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    members: Mapped[list["LeagueMember"]] = relationship(
        back_populates="league", cascade="all, delete-orphan"
    )


class LeagueMember(Base):
    __tablename__ = "league_members"
    __table_args__ = (UniqueConstraint("league_id", "user_id", name="uq_league_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    bank_balance: Mapped[int] = mapped_column(
        BigInteger, default=STARTING_BUDGET, nullable=False
    )

    league: Mapped["League"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")  # noqa: F821
