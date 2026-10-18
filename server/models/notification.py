from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.enums import NotificationKind


class Notification(Base):
    """An email sent to a user about a race — one per kind per race, so the
    scheduled job never sends the same reminder twice."""

    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "race_id", "kind", name="uq_notification"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    race_id: Mapped[int] = mapped_column(
        ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[NotificationKind] = mapped_column(
        SAEnum(NotificationKind, native_enum=False, length=32), nullable=False
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False
    )
