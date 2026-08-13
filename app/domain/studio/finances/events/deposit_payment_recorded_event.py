from decimal import Decimal
from uuid import UUID


class DepositPaymentRecordedEvent:
    def __init__(
        self,
        *,
        appointment_id: UUID,
        amount: Decimal,
    ):
        self.appointment_id = appointment_id
        self.amount = amount
