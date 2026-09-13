from dataclasses import dataclass
from uuid import UUID

from app.domain.studio.users.entities.user import User


@dataclass(frozen=True)
class CancelAppointmentInput:
    appointment_id: UUID
    actor: User
    reason: str
