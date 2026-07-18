from datetime import datetime, timezone
from uuid import UUID

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.create_appointment_dto import CreateAppointmentInput
from app.core.exceptions.appointments import SlotIsAlreadyOccupiedError
from app.core.exceptions.calendar import (
    CannotFindWorkingPeriodsForThisUserError,
)
from app.core.types.audit_actor_type import AuditActorType
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)


# TODO: fazer a rota e o script que usam esse use_case e testar o use_case a rota e o script
class CreateAppointmentUseCase:
    def __init__(
        self,
        uow: WriteUnitOfWork,
        integration_bus: IntegrationEventBus,
        calendar_policy: CalendarAvailabilityPolicy,
    ):
        self.uow = uow
        self.integration_bus = integration_bus
        self.calendar_policy = calendar_policy

    async def execute(self, data: CreateAppointmentInput) -> None:
        with self.uow:
            calendar_of_user = self.uow.calendar_settings.find_by_user_id(data.user_id)
            if not calendar_of_user:
                raise CannotFindWorkingPeriodsForThisUserError()

            can_ignore_booking_window = self.__can_ignore_booking_window(
                user_id=data.actor_id, calendar_user=data.user_id
            )

            calendar_exceptions_overlap = self.uow.calendar_exceptions.find_overlap(
                user_id=data.user_id, start_at=data.start_at, end_at=data.end_at
            )

            # TODO: ao chamar esse use_case no script e na rota fazer o tratamento de erros para os erros da policy
            self.calendar_policy.can_schedule(
                calendar_settings=calendar_of_user,
                calendar_exceptions=calendar_exceptions_overlap,
                can_ignore_booking_window=can_ignore_booking_window,
                start_at=data.start_at,
                end_at=data.end_at,
            )

            occupied_slot = self.uow.appointments.find_overlap(
                start_date=data.start_at, end_date=data.end_at, user_id=data.user_id
            )

            if occupied_slot:
                raise SlotIsAlreadyOccupiedError()

            await self._save_appointment(data)

    def _make_appointment(self, data: CreateAppointmentInput):
        if data.actor_id is not None:
            actor_type = AuditActorType.USER
        else:
            actor_type = AuditActorType.SYSTEM

        appointment = Appointment.create(
            user_id=data.user_id,
            appointment_type=data.appointment_type,
            client_info=data.client_info,
            color=data.color,
            start_at=data.start_at,
            end_at=data.end_at,
            details=data.details,
            placement=data.placement,
            referral_code=data.referral_code,
            size=data.size,
        )
        log = AuditLogEntry(
            entity_name="appointments",
            entity_id=appointment.id,
            action="create appointment",
            actor_id=data.actor_id,
            actor_type=actor_type,
            changes={
                "initial_state_must_important_info": {
                    "appointment_on_calendar_of": data.user_id,
                    "appointment_type": data.appointment_type,
                    "client_info": data.client_info,
                    "start_at": data.start_at,
                    "end_at": data.end_at,
                    "referral_code": data.referral_code,
                }
            },
            performed_at=datetime.now(timezone.utc),
        )

        return appointment, log

    async def _save_appointment(self, data: CreateAppointmentInput):
        appointment, log = self._make_appointment(data)

        self.uow.appointments.create(appointment)
        self.uow.audit_logs.create(log)

        await self.integration_bus.publish(appointment.create_appointment_request())

    def __can_ignore_booking_window(self, *, user_id: UUID | None, calendar_user: UUID) -> bool:
        if user_id is None:
            return False

        user = self.uow.users.find_by_id(user_id)

        if user is None:
            return False

        if user.is_admin:
            return True

        return user.id == calendar_user
