import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.doctor import DoctorRepository
from app.repositories.appointment import AppointmentRepository
from app.models.site import Site
from app.core import calcom_client
from app.core.composio_client import append_lead_to_sheet
from app.core.make_webhook_client import append_lead_via_make
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doctor_repo = DoctorRepository(db)
        self.appointment_repo = AppointmentRepository(db)

    async def list_doctors(self, site_id: uuid.UUID) -> list[dict]:
        doctors = await self.doctor_repo.get_all(site_id)
        return [
            {"id": str(d.id), "name": d.name, "specialty": d.specialty}
            for d in doctors
        ]

    async def get_availability(self, doctor_id: uuid.UUID, site_id: uuid.UUID, start_date: str, end_date: str) -> list[str]:
        doctor = await self.doctor_repo.get_by_id(doctor_id, site_id)
        if not doctor:
            raise NotFoundError("Doctor not found.")
        try:
            return await calcom_client.get_available_slots(doctor.cal_event_type_id, start_date, end_date)
        except calcom_client.CalComError as e:
            raise BadRequestError(f"Could not check availability: {e}")

    async def book_appointment(
        self,
        site_id: uuid.UUID,
        doctor_id: uuid.UUID,
        start_iso: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str | None = None,
        customer_timezone: str = "UTC",
    ) -> dict:
        doctor = await self.doctor_repo.get_by_id(doctor_id, site_id)
        if not doctor:
            raise NotFoundError("Doctor not found.")

        # Book on Cal.com first -- if this fails, there's nothing to save.
        try:
            cal_result = await calcom_client.create_booking(
                event_type_id=doctor.cal_event_type_id,
                start_iso=start_iso,
                attendee_name=customer_name,
                attendee_email=customer_email,
                attendee_timezone=customer_timezone,
                attendee_phone=customer_phone,
            )
            cal_booking_uid = cal_result.get("uid")
        except calcom_client.CalComError as e:
            raise BadRequestError(f"Could not book appointment: {e}")

        appointment = await self.appointment_repo.create(
            site_id=site_id,
            doctor_id=doctor_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            scheduled_at=datetime.fromisoformat(start_iso.replace("Z", "+00:00")),
            cal_booking_uid=cal_booking_uid,
        )
        logger.info(f"Appointment booked: {appointment.id} with doctor {doctor_id}")

        # Best-effort -- never let a Sheets/email hiccup undo a real booking.
        # Make.com is tried first (simpler webhook setup); Composio as a
        # fallback if you get that working later. This one webhook call
        # carries everything needed to drive two actions in the same Make
        # scenario -- adding the row to Sheets AND sending the confirmation
        # email -- so no separate email webhook is needed for this one.
        site_result = await self.db.execute(select(Site).where(Site.id == site_id))
        site = site_result.scalar_one_or_none()
        note = f"Booked with Dr. {doctor.name} on {start_iso}"
        pushed = await append_lead_via_make(
            name=customer_name, email=customer_email, phone=customer_phone, note=note,
            site_name=site.name if site else "", doctor_name=doctor.name, scheduled_at=start_iso,
        )
        if not pushed:
            await append_lead_to_sheet(
                name=customer_name, email=customer_email, phone=customer_phone, note=note,
            )

        return {
            "appointment_id": str(appointment.id),
            "doctor_name": doctor.name,
            "scheduled_at": start_iso,
        }

    async def list_appointments(self, site_id: uuid.UUID, page: int = 1, page_size: int = 20) -> list[dict]:
        appointments = await self.appointment_repo.list_for_site(site_id, page, page_size)
        return [
            {
                "id": str(a.id),
                "doctor_id": str(a.doctor_id),
                "doctor_name": a.doctor.name if a.doctor else "Unknown",
                "customer_name": a.customer_name,
                "customer_email": a.customer_email,
                "customer_phone": a.customer_phone,
                "scheduled_at": a.scheduled_at.isoformat(),
                "status": a.status.value,
                "created_at": a.created_at.isoformat(),
            }
            for a in appointments
        ]