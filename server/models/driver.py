from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (
        UniqueConstraint("driver_number", "season", name="uq_driver_number_season"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    driver_number: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str | None] = mapped_column(String, nullable=True)  # 3-letter, e.g. VER
    constructor_id: Mapped[int] = mapped_column(
        ForeignKey("constructors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    salary: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # On the current grid. Stand-ins who raced once stay in the table (their
    # results and scores reference them) but can't be signed.
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    season: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    constructor: Mapped["Constructor"] = relationship(back_populates="drivers")  # noqa: F821
