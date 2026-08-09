from decimal import Decimal
from uuid import UUID

from app.core.types.appointment_enums import AppointmentType


class NotifyOfAppointmentQuoted:
    def __init__(
        self,
        *,
        appointment_type: AppointmentType,
        client_email_or_vip_id: str | UUID,
        price: Decimal,
    ):
        self.appointment_type = appointment_type
        self.client_email_or_vip_id = client_email_or_vip_id
        self.price = price
