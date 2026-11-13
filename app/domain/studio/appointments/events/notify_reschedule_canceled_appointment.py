from datetime import datetime
from uuid import UUID

from app.core.types.appointment_enums import AppointmentStatus, AppointmentType


class NotifyRescheduleCanceledAppointment:
    def __init__(
        self,
        *,
        old_appointment_id: UUID,
        new_appointment_id: UUID,
        status: AppointmentStatus,
        has_confirmed_deposit: bool,
        start_at: datetime,
        end_at: datetime,
        appointment_type: AppointmentType,
        user_id: UUID,
        client_email_or_vip_id: str | UUID,
    ):
        self.old_appointment_id = old_appointment_id
        self.new_appointment_id = new_appointment_id
        self.status = status
        self.has_confirmed_deposit = has_confirmed_deposit
        self.start_at = start_at
        self.end_at = end_at
        self.appointment_type = appointment_type
        self.user_id = user_id
        self.client_email_or_vip_id = client_email_or_vip_id
