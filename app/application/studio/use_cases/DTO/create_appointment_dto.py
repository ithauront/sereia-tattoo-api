from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.value_objects.client_code import ClientCode


@dataclass(frozen=True)
class CreateAppointmentInput:
    appointment_type: AppointmentType
    user_id: UUID
    start_at: datetime
    end_at: datetime
    placement: str
    details: str
    client_info: ClientInfo
    total_sessions: int | None = None
    project_id: UUID | None = None
    size: str | None = None
    color: bool = False

    referral_code: ClientCode | None = None

    actor_id: UUID | None = None


@dataclass(frozen=True)
class CreateAppointmentOutput:
    appointment_id: UUID
    project_id: UUID | None
    current_session: int | None
    total_sessions: int | None
