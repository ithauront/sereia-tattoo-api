from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.value_objects.client_code import ClientCode


class CreateAppointmentInput(BaseModel):
    appointment_type: AppointmentType
    user_id: UUID
    start_at: datetime
    end_at: datetime
    placement: str
    details: str
    size: str | None = None
    color: bool = False
    client_info: ClientInfo
    referral_code: ClientCode | None = None

    actor_id: UUID | None = None
