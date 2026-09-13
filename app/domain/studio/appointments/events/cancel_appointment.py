from datetime import datetime
from uuid import UUID

from app.core.types.appointment_enums import AppointmentType


class CancelAppointmentEmailRequested:
    def __init__(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        appointment_type: AppointmentType,
        user_id: UUID,
        client_email_or_vip_id: str | UUID,
        has_confirmed_deposit: bool,
        is_eligible_for_deposit_refund: bool,
    ):
        self.start_at = start_at
        self.end_at = end_at
        self.appointment_type = appointment_type
        self.user_id = user_id
        self.client_email_or_vip_id = client_email_or_vip_id
        self.has_confirmed_deposit = has_confirmed_deposit
        self.is_eligible_for_deposit_refund = is_eligible_for_deposit_refund
