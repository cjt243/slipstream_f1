from sqlalchemy import BigInteger, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Constructor(Base):
    __tablename__ = "constructors"
    __table_args__ = (UniqueConstraint("name", "season", name="uq_constructor_season"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str | None] = mapped_column(String, nullable=True)  # team hex, e.g. #3671C6
    salary: Mapped[int] = mapped_column(BigInteger, nullable=False)
    season: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    drivers: Mapped[list["Driver"]] = relationship(back_populates="constructor")  # noqa: F821
