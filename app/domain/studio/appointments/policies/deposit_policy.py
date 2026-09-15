from datetime import datetime, timedelta

from app.domain.studio.appointments.entities.appointment import Appointment


class DepositPolicy:
    def is_deposit_refund_eligible(self, appointment: Appointment, canceled_at: datetime) -> bool:
        return (
            appointment.deposit_confirmed_at is not None
            and appointment.start_at - canceled_at >= timedelta(hours=48)
        )

    def is_deposit_trasferable_on_reschedule(
        self, appointment: Appointment, reschedule_at: datetime
    ) -> bool:
        return self.is_deposit_refund_eligible(appointment=appointment, canceled_at=reschedule_at)
