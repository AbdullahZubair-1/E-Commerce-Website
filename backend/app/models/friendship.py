import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base


class FriendRequestStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class FriendRequest(Base):
    """A friend request between two users on the SAME site. Once accepted,
    this same row represents the friendship (status=ACCEPTED) -- there's no
    separate "friendship" table."""

    __tablename__ = "friend_requests"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friend_requests_pair"),
        CheckConstraint("requester_id != addressee_id", name="ck_friend_requests_not_self"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    addressee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[FriendRequestStatus] = mapped_column(
        SAEnum(FriendRequestStatus), default=FriendRequestStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id])  # type: ignore
    addressee: Mapped["User"] = relationship("User", foreign_keys=[addressee_id])  # type: ignore

    def __repr__(self) -> str:
        return f"<FriendRequest {self.requester_id} -> {self.addressee_id} ({self.status})>"