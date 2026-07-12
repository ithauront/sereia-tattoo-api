from uuid import UUID

from app.domain.studio.value_objects.client_code import ClientCode


class CreateAppointmentEmailRequested:
    def __init__(
        self, *, appointment_id: UUID, user_id: UUID, client_email_or_vip_code: str | ClientCode
    ):
        self.appointment_id = appointment_id
        self.user_id = user_id
        self.client_email_or_vip_code = client_email_or_vip_code
