from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.studio.users.entities.user import User


@dataclass
class QuoteAppointmentInput:
    actor: User
    appointment_id: UUID
    price: Decimal
