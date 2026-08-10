from datetime import datetime, timezone

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.quote_appointement_dto import QuoteAppointmentInput
from app.core.exceptions.appointments import (
    AppointmentNotFoundError,
)
from app.core.types.audit_actor_type import AuditActorType
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)


class QuoteAppointmentUseCase:
    def __init__(
        self,
        write_uow: WriteUnitOfWork,
        read_uow: ReadUnitOfWork,
        integration_bus: IntegrationEventBus,
        appointment_authorization_policy: AppointmentAuthorizationPolicy,
    ):
        self.write_uow = write_uow
        self.read_uow = read_uow
        self.integration_bus = integration_bus
        self.appointment_authorization_policy = appointment_authorization_policy

    async def execute(self, data: QuoteAppointmentInput):
        with self.write_uow:
            appointment = self.write_uow.appointments.find_by_id(data.appointment_id)

            if not appointment:
                raise AppointmentNotFoundError()

            self.appointment_authorization_policy.ensure_admin_or_owner(
                actor=data.actor, appointment=appointment
            )

            appointment.quote(price=data.price)
            self.write_uow.appointments.update(appointment)

            log = AuditLogEntry(
                entity_name="appointments",
                entity_id=appointment.id,
                action="quote appointment",
                actor_id=data.actor.id,
                actor_type=AuditActorType.USER,
                changes={
                    "price_quoted": str(appointment.price),
                },
                performed_at=datetime.now(timezone.utc),
            )
            self.write_uow.audit_logs.create(log)

        await self.integration_bus.publish(
            appointment.notify_of_appointment_quoted(),
            uow=self.read_uow,
        )
