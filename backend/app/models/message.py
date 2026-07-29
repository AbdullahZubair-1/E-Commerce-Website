import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base


class Message(Base):
    """A single direct message between two friends. Only allowed between
    users who are already friends (accepted FriendRequest) on the same
    site -- enforced at the service layer, not by the schema."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("sender_id != recipient_id", name="ck_messages_not_self"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])  # type: ignore
    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id])  # type: ignore

    def __repr__(self) -> str:
        return f"<Message {self.sender_id} -> {self.recipient_id}>"