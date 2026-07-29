import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.appointment import Appointment


class AppointmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        site_id: uuid.UUID,
        doctor_id: uuid.UUID,
        customer_name: str,
        customer_email: str,
        scheduled_at,
        customer_phone: str | None = None,
        cal_booking_uid: str | None = None,
    ) -> Appointment:
        appointment = Appointment(
            site_id=site_id,
            doctor_id=doctor_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            scheduled_at=scheduled_at,
            cal_booking_uid=cal_booking_uid,
        )
        self.db.add(appointment)
        await self.db.flush()
        await self.db.refresh(appointment)
        return appointment

    async def list_for_site(self, site_id: uuid.UUID, page: int = 1, page_size: int = 20) -> list[Appointment]:
        result = await self.db.execute(
            select(Appointment)
            .options(selectinload(Appointment.doctor))
            .where(Appointment.site_id == site_id)
            .order_by(Appointment.scheduled_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all())