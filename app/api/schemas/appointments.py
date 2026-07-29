from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.types.appointment_enums import AppointmentType


class CreateAppointmentRequest(BaseModel):
    appointment_type: AppointmentType
    user_id: UUID
    start_at: datetime
    end_at: datetime
    placement: str
    details: str
    size: str | None
    color: bool

    vip_client_id: UUID | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    referral_code: str | None = None
