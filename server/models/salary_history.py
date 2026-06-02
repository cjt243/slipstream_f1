from sqlalchemy import BigInteger, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.enums import ElementType


class SalaryHistory(Base):
    """One row per element per race recording the salary change applied."""

    __tablename__ = "salary_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    element_type: Mapped[ElementType] = mapped_column(
        SAEnum(ElementType, native_enum=False, length=16), nullable=False
    )
    element_id: Mapped[int] = mapped_column(Integer, nullable=False)
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False
    )
    salary_before: Mapped[int] = mapped_column(BigInteger, nullable=False)
    salary_after: Mapped[int] = mapped_column(BigInteger, nullable=False)
