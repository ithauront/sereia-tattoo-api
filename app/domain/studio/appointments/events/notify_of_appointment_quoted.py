from decimal import Decimal
from uuid import UUID

from app.core.types.appointment_enums import AppointmentType


class NotifyOfAppointmentQuoted:
    def __init__(
        self,
        *,
        appointment_type: AppointmentType,
        client_email_or_vip_id: str | UUID,
        total_sessions: int | None = None,
        current_session: int | None = None,
        price: Decimal,
    ):
        self.appointment_type = appointment_type
        self.client_email_or_vip_id = client_email_or_vip_id
        self.total_sessions = total_sessions
        self.current_session = current_session
        self.price = price
