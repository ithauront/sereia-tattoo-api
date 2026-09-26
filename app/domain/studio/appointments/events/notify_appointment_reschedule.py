from datetime import datetime
from uuid import UUID

from app.core.types.appointment_enums import AppointmentType


class NotifyOfAppointmentReschedule:
    def __init__(
        self,
        *,
        user_id: UUID,
        appointment_type: AppointmentType,
        client_email_or_vip_id: str | UUID,
        start_at: datetime,
        end_at: datetime,
        was_deposit_retained: bool,
    ):
        self.user_id = user_id
        self.appointment_type = appointment_type
        self.client_email_or_vip_id = client_email_or_vip_id
        self.start_at = start_at
        self.end_at = end_at
        self.was_deposit_retained = was_deposit_retained
