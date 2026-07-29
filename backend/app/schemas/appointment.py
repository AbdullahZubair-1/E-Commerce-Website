import uuid
from datetime import datetime
from pydantic import BaseModel


class DoctorCreate(BaseModel):
    name: str
    specialty: str | None = None
    cal_event_type_id: str


class DoctorUpdate(BaseModel):
    name: str | None = None
    specialty: str | None = None
    cal_event_type_id: str | None = None
    is_active: bool | None = None


class DoctorResponse(BaseModel):
    id: uuid.UUID
    name: str
    specialty: str | None
    cal_event_type_id: str
    is_active: bool

    model_config = {"from_attributes": True}


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    doctor_name: str
    customer_name: str
    customer_email: str
    customer_phone: str | None
    scheduled_at: datetime
    status: str
    created_at: datetime