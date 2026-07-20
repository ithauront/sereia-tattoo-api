from datetime import datetime
from uuid import UUID

from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.value_objects.client_code import ClientCode


class CreateAppointmentEmailRequested:
    def __init__(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        appointment_type: AppointmentType,
        user_id: UUID,
        client_email_or_vip_code: str | ClientCode,
    ):
        self.start_at = start_at
        self.end_at = end_at
        self.appointment_type = appointment_type
        self.user_id = user_id
        self.client_email_or_vip_code = client_email_or_vip_code
