import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base


class AppointmentStatus(str, PyEnum):
    BOOKED = "booked"
    CANCELLED = "cancelled"


class Appointment(Base):
    """A booked doctor appointment. Recorded locally regardless of whether
    the Cal.com booking or the Composio lead-sheet push succeed, so the
    admin always has a record even if an external service is down."""

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(AppointmentStatus), default=AppointmentStatus.BOOKED, nullable=False
    )
    # The booking's unique ID on Cal.com's side, so it can be looked up /
    # cancelled later. Null if the Cal.com call failed but we still recorded
    # the appointment locally.
    cal_booking_uid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    site: Mapped["Site"] = relationship("Site")  # type: ignore
    doctor: Mapped["Doctor"] = relationship("Doctor")  # type: ignore

    def __repr__(self) -> str:
        return f"<Appointment {self.customer_name} -> {self.doctor_id} @ {self.scheduled_at}>"