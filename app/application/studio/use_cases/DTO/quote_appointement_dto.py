from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.studio.users.entities.user import User


@dataclass(frozen=True)
class QuoteAppointmentInput:
    actor: User
    appointment_id: UUID
    price: Decimal
    total_sessions: int | None = None


@dataclass(frozen=True)
class QuoteAppointmentOutput:
    appointment_id: UUID
    project_id: UUID | None
    current_session: int | None
    total_sessions: int | None
