import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base


class Doctor(Base):
    """A doctor customers can book an appointment with. Scoped per site, same
    as everything else -- Chemisto and Chemisto Food each manage their own
    doctor list. Booking itself happens against Cal.com using
    cal_event_type_id, which the store owner sets up on their Cal.com
    account (one Cal.com "event type" per doctor)."""

    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    specialty: Mapped[str | None] = mapped_column(String(150), nullable=True)
    # The Cal.com "event type" ID that represents this doctor's bookable
    # calendar. Created by the store owner in their own Cal.com account.
    cal_event_type_id: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    site: Mapped["Site"] = relationship("Site")  # type: ignore

    def __repr__(self) -> str:
        return f"<Doctor {self.name} ({self.specialty})>"