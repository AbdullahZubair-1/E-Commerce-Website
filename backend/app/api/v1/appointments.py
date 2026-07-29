import uuid
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.base import success_response
from app.schemas.appointment import DoctorCreate, DoctorUpdate
from app.services.appointment import AppointmentService
from app.repositories.doctor import DoctorRepository
from app.dependencies.auth import get_current_owner
from app.dependencies.site import get_current_site
from app.models.user import User
from app.models.site import Site

router = APIRouter(prefix="/appointments", tags=["Appointments"])


class BookAppointmentRequest(BaseModel):
    doctor_id: uuid.UUID
    start_iso: str
    customer_name: str
    customer_email: EmailStr
    customer_phone: str | None = None
    customer_timezone: str = "UTC"


# --- Public routes: called by Ana (text + voice) and, in principle, a future booking page ---

@router.get("/doctors")
async def list_doctors(
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """List doctors available for booking on this site (public, site-scoped)."""
    service = AppointmentService(db)
    result = await service.list_doctors(site.id)
    return success_response(data=result, message="Doctors retrieved.")


@router.get("/availability")
async def get_availability(
    doctor_id: uuid.UUID,
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """Get a doctor's available booking slots between two dates (public, site-scoped)."""
    service = AppointmentService(db)
    slots = await service.get_availability(doctor_id, site.id, start_date, end_date)
    return success_response(data={"slots": slots}, message="Availability retrieved.")


@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_appointment(
    data: BookAppointmentRequest,
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """Book an appointment with a doctor (public, site-scoped). Not gated
    behind customer login -- Ana collects the customer's name/email/phone
    directly during the conversation, the same way over voice or text."""
    service = AppointmentService(db)
    result = await service.book_appointment(
        site_id=site.id,
        doctor_id=data.doctor_id,
        start_iso=data.start_iso,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        customer_phone=data.customer_phone,
        customer_timezone=data.customer_timezone,
    )
    return success_response(data=result, message="Appointment booked.")


# --- Owner-only admin routes ---

@router.get("/admin/list")
async def list_appointments_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    service = AppointmentService(db)
    result = await service.list_appointments(owner.site_id, page, page_size)
    return success_response(data=result, message="Appointments retrieved.")


@router.get("/admin/doctors")
async def list_doctors_admin(
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    repo = DoctorRepository(db)
    doctors = await repo.get_all(owner.site_id, active_only=False)
    return success_response(
        data=[
            {
                "id": str(d.id),
                "name": d.name,
                "specialty": d.specialty,
                "cal_event_type_id": d.cal_event_type_id,
                "is_active": d.is_active,
            }
            for d in doctors
        ],
        message="Doctors retrieved.",
    )


@router.post("/admin/doctors", status_code=status.HTTP_201_CREATED)
async def create_doctor(
    data: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    repo = DoctorRepository(db)
    doctor = await repo.create(
        site_id=owner.site_id,
        name=data.name,
        cal_event_type_id=data.cal_event_type_id,
        specialty=data.specialty,
    )
    return success_response(
        data={"id": str(doctor.id), "name": doctor.name, "specialty": doctor.specialty},
        message="Doctor added.",
    )


@router.put("/admin/doctors/{doctor_id}")
async def update_doctor(
    doctor_id: uuid.UUID,
    data: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    repo = DoctorRepository(db)
    doctor = await repo.get_by_id(doctor_id, owner.site_id)
    if not doctor:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Doctor not found.")
    updates = data.model_dump(exclude_none=True)
    doctor = await repo.update(doctor, **updates)
    return success_response(
        data={"id": str(doctor.id), "name": doctor.name, "is_active": doctor.is_active},
        message="Doctor updated.",
    )