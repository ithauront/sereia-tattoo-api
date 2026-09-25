from datetime import datetime, timedelta, timezone
from typing import List

from app.core.types.payment_enums import PaymentAllocationStatus, PaymentPurposeType
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.finances.entities.payment import Payment


class DepositPolicy:
    def is_deposit_refund_eligible(self, appointment: Appointment, canceled_at: datetime) -> bool:
        return (
            appointment.deposit_confirmed_at is not None
            and appointment.start_at - canceled_at >= timedelta(hours=48)
        )

    def is_deposit_transferable_on_reschedule(
        self, *, appointment: Appointment, payments: List[Payment], reschedule_at: datetime
    ) -> bool:
        has_active_deposit = any(
            payment.appointment_id == appointment.id
            and payment.payment_purpose == PaymentPurposeType.DEPOSIT
            and payment.allocation_status == PaymentAllocationStatus.ACTIVE
            for payment in payments
        )
        return (
            has_active_deposit
            and appointment.deposit_confirmed_at is not None
            and (appointment.start_at.astimezone(timezone.utc) - reschedule_at.astimezone(timezone.utc))
            >= timedelta(hours=48)
        )
