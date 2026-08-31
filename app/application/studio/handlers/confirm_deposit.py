from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.core.exceptions.appointments import (
    AppointmentNotFoundError,
)
from app.domain.studio.finances.events.deposit_payment_recorded_event import DepositPaymentRecordedEvent


class ConfirmDepositHandler:
    async def handle(self, event: DepositPaymentRecordedEvent, *, uow: WriteUnitOfWork) -> None:

        appointment = uow.appointments.find_by_id(event.appointment_id)

        if not appointment:
            raise AppointmentNotFoundError()

        appointment.confirm_deposit()

        uow.appointments.update(appointment)
