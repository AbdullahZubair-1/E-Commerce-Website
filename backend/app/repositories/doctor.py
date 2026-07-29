import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.doctor import Doctor


class DoctorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, site_id: uuid.UUID, active_only: bool = True) -> list[Doctor]:
        query = select(Doctor).where(Doctor.site_id == site_id)
        if active_only:
            query = query.where(Doctor.is_active == True)  # noqa: E712
        result = await self.db.execute(query.order_by(Doctor.name))
        return list(result.scalars().all())

    async def get_by_id(self, doctor_id: uuid.UUID, site_id: uuid.UUID) -> Optional[Doctor]:
        result = await self.db.execute(
            select(Doctor).where(Doctor.id == doctor_id, Doctor.site_id == site_id)
        )
        return result.scalar_one_or_none()

    async def create(self, site_id: uuid.UUID, name: str, cal_event_type_id: str, specialty: str | None = None) -> Doctor:
        doctor = Doctor(site_id=site_id, name=name, specialty=specialty, cal_event_type_id=cal_event_type_id)
        self.db.add(doctor)
        await self.db.flush()
        await self.db.refresh(doctor)
        return doctor

    async def update(self, doctor: Doctor, **kwargs) -> Doctor:
        for key, value in kwargs.items():
            if hasattr(doctor, key) and value is not None:
                setattr(doctor, key, value)
        await self.db.flush()
        await self.db.refresh(doctor)
        return doctor