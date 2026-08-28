from datetime import datetime, timezone

from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.complete_paid_appointment_dto import (
    CompletePaidAppointmentInput,
)
from app.core.exceptions.appointments import (
    AppointmentHasPendingRefundError,
    AppointmentNotFoundError,
    AppointmentWasNotFullyPaidError,
    PriceMustBeDefinedError,
)
from app.core.types.audit_actor_type import AuditActorType
from app.domain.studio.finances.entities.value_objects.appointment_payment_summary import (
    AppointmentPaymentSummary,
)


class CompletePaidAppointmentUseCase:
    def __init__(self, uow: WriteUnitOfWork, transactional_bus: TransactionalEventBus):
        self.uow = uow
        self.transactional_bus = transactional_bus

    async def execute(self, data: CompletePaidAppointmentInput) -> None:
        with self.uow:
            appointment = self.uow.appointments.find_by_id(appointment_id=data.appointment_id)

            if appointment is None:
                raise AppointmentNotFoundError()

            if appointment.price is None:
                raise PriceMustBeDefinedError()

            previous_status = appointment.status

            total_paid = self.uow.payments.sum_payable_by_appointment_id(appointment_id=appointment.id)

            total_completed_refunds = self.uow.refunds.sum_completed_by_payable_payments_for_appointment(
                appointment_id=appointment.id,
            )

            total_pending_refunds = self.uow.refunds.sum_pending_by_payable_payments_for_appointment(
                appointment_id=appointment.id,
            )

            payment_summary = AppointmentPaymentSummary(
                total_paid=total_paid,
                total_completed_refunds=total_completed_refunds,
                total_pending_refunds=total_pending_refunds,
            )

            if payment_summary.has_pending_refunds:
                raise AppointmentHasPendingRefundError()

            if payment_summary.net_paid < appointment.price:
                raise AppointmentWasNotFullyPaidError("please_check_payments_and_possible_refunds")

            event = appointment.complete(total_paid=payment_summary.net_paid)

            self.uow.appointments.update(appointment=appointment)

            log = AuditLogEntry(
                entity_name="appointments",
                entity_id=appointment.id,
                action="mark appointment as completed and paid",
                actor_id=data.actor_id,
                actor_type=AuditActorType.USER,
                changes={
                    "status": {
                        "from": previous_status.value,
                        "to": appointment.status.value,
                    },
                    "payment": {
                        "total_paid": payment_summary.net_paid,
                    },
                },
                performed_at=datetime.now(timezone.utc),
            )

            self.uow.audit_logs.create(log)

            if event is not None:
                await self.transactional_bus.publish(event, uow=self.uow)

            """
            The event triggers a handler responsible for creating client credits
            when there is a referral.

            Since client credits are a financial right of the client,
            their creation should happen in the same transaction
            as the appointment completion.
            """
