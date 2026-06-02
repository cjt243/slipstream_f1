from sqlalchemy import BigInteger, Boolean, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.enums import ElementType


class Contract(Base):
    """A user's signing of a driver or constructor for 1–5 races.

    ``element_id`` references either a driver or a constructor depending on
    ``element_type`` (kept polymorphic by type rather than two FK columns).
    """

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="CASCADE"), index=True, nullable=False
    )
    element_type: Mapped[ElementType] = mapped_column(
        SAEnum(ElementType, native_enum=False, length=16), nullable=False
    )
    element_id: Mapped[int] = mapped_column(Integer, nullable=False)
    race_start: Mapped[int] = mapped_column(Integer, nullable=False)  # round signed for
    contract_length: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    signed_salary: Mapped[int] = mapped_column(BigInteger, nullable=False)
    released_early: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Round at which the element left the roster (early release OR expiry) —
    # drives the one-race re-sign cooldown. Null while active.
    released_at_race: Mapped[int | None] = mapped_column(Integer, nullable=True)
