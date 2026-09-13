from datetime import datetime, timezone

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.cancel_appointment import CancelAppointmentInput
from app.core.exceptions.appointments import AppointmentNotFoundError
from app.core.types.audit_actor_type import AuditActorType
from app.core.validations.text import validate_text
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from app.domain.studio.appointments.policies.deposit_policy import DepositPolicy


class CancelAppointmentUseCase:
    def __init__(
        self,
        write_uow: WriteUnitOfWork,
        read_uow: ReadUnitOfWork,
        integration_bus: IntegrationEventBus,
        appointment_authorization_policy: AppointmentAuthorizationPolicy,
        deposit_policy: DepositPolicy,
    ):
        self.write_uow = write_uow
        self.read_uow = read_uow
        self.integration_bus = integration_bus
        self.appointment_authorization_policy = appointment_authorization_policy
        self.deposit_policy = deposit_policy

    async def execute(self, data: CancelAppointmentInput):
        with self.write_uow:
            appointment = self.write_uow.appointments.find_by_id(data.appointment_id)

            if appointment is None:
                raise AppointmentNotFoundError()

            self.appointment_authorization_policy.ensure_admin_or_owner(
                actor=data.actor, appointment=appointment
            )
            cancellation_reason = validate_text(data.reason)

            appointment_status_before = appointment.status

            now = datetime.now(timezone.utc)
            is_eligible_for_deposit_refund = self.deposit_policy.is_deposit_refund_eligible(
                appointment=appointment, canceled_at=now
            )

            event = appointment.mark_as_canceled(
                observations=cancellation_reason,
                is_eligible_for_deposit_refund=is_eligible_for_deposit_refund,
            )

            self.write_uow.appointments.update(appointment)

            log = AuditLogEntry(
                entity_name="appointments",
                entity_id=appointment.id,
                action="cancel appointment",
                actor_id=data.actor.id,
                actor_type=AuditActorType.USER,
                changes={
                    "status": {
                        "from": appointment_status_before.value,
                        "to": appointment.status.value,
                    },
                    "is_eligible_for_deposit_refund": is_eligible_for_deposit_refund,
                },
                performed_at=now,
                reason=cancellation_reason,
            )
            self.write_uow.audit_logs.create(log)

        await self.integration_bus.publish(
            event,
            uow=self.read_uow,
        )
