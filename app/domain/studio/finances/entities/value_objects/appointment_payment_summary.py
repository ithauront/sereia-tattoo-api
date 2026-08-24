from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AppointmentPaymentSummary:
    total_paid: Decimal
    total_completed_refunds: Decimal
    total_pending_refunds: Decimal

    @property
    def net_paid(self) -> Decimal:
        return self.total_paid - self.total_completed_refunds - self.total_pending_refunds

    @property
    def has_pending_refunds(self) -> bool:
        return self.total_pending_refunds > Decimal("0")
