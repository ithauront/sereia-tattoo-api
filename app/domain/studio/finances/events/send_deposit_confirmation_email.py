from datetime import datetime
from decimal import Decimal

from app.core.types.appointment_enums import AppointmentType


class SendDepositConfirmationEmailEvent:
    def __init__(
        self,
        *,
        client_email: str,
        amount: Decimal,
        appointment_type: AppointmentType,
        start_at: datetime,
    ):
        self.client_email = client_email
        self.amount = amount
        self.appointment_type = appointment_type
        self.start_at = start_at
