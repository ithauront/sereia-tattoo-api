from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.create_appointment_dto import (
    CreateAppointmentInput,
    CreateAppointmentOutput,
)
from app.core.exceptions.appointments import (
    AppointmentProjectNotFoundError,
    AppointmentProjectRequiresAuthenticatedUserError,
    SlotIsAlreadyOccupiedError,
    TotalSessionsMustMatchProjectError,
)
from app.core.exceptions.calendar import (
    CannotFindWorkingPeriodsForThisUserError,
)
from app.core.exceptions.users import UserInactiveError, UserNotFoundError
from app.core.types.audit_actor_type import AuditActorType
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.appointments.policies.appointment_project_policy import (
    AppointmentProjectPolicy,
)
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)


class CreateAppointmentUseCase:
    def __init__(
        self,
        write_uow: WriteUnitOfWork,
        read_uow: ReadUnitOfWork,
        integration_bus: IntegrationEventBus,
        calendar_policy: CalendarAvailabilityPolicy,
        project_policy: AppointmentProjectPolicy,
    ):
        self.write_uow = write_uow
        self.read_uow = read_uow
        self.integration_bus = integration_bus
        self.calendar_policy = calendar_policy
        self.project_policy = project_policy

    async def execute(self, data: CreateAppointmentInput) -> CreateAppointmentOutput:
        self._ensure_actor_can_manage_project(data)

        with self.write_uow:
            user = self.write_uow.users.find_by_id(data.user_id)
            if not user:
                raise UserNotFoundError()
            if user.is_active is False:
                raise UserInactiveError()

            calendar_of_user = self.write_uow.calendar_settings.find_by_user_id(data.user_id)
            if not calendar_of_user:
                raise CannotFindWorkingPeriodsForThisUserError()

            can_ignore_booking_window = self.__can_ignore_booking_window(
                user_id=data.actor_id, calendar_user=data.user_id
            )

            calendar_exceptions_overlap = self.write_uow.calendar_exceptions.find_overlap(
                user_id=data.user_id, start_at=data.start_at, end_at=data.end_at
            )

            self.calendar_policy.can_schedule(
                calendar_settings=calendar_of_user,
                calendar_exceptions=calendar_exceptions_overlap,
                can_ignore_booking_window=can_ignore_booking_window,
                start_at=data.start_at,
                end_at=data.end_at,
            )

            occupied_slot = self.write_uow.appointments.find_overlap(
                start_date=data.start_at, end_date=data.end_at, user_id=data.user_id
            )

            if occupied_slot:
                raise SlotIsAlreadyOccupiedError()

            appointment = await self._save_appointment(data)

        return CreateAppointmentOutput(
            appointment_id=appointment.id,
            project_id=appointment.project_id,
            current_session=appointment.current_session,
            total_sessions=appointment.total_sessions,
        )

    def _ensure_actor_can_manage_project(self, data: CreateAppointmentInput) -> None:
        if data.project_id is None and data.total_sessions is None:
            return

        if data.actor_id is None:
            raise AppointmentProjectRequiresAuthenticatedUserError()

        actor = self.read_uow.users.find_by_id(data.actor_id)
        if actor is None or not actor.is_active:
            raise AppointmentProjectRequiresAuthenticatedUserError()

    def _make_appointment(self, data: CreateAppointmentInput):
        if data.actor_id is not None:
            actor_type = AuditActorType.USER
        else:
            actor_type = AuditActorType.CLIENT

        project_id, current_session, total_sessions = self._resolve_appointment_project(
            project_id=data.project_id, total_sessions=data.total_sessions
        )

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
            total_sessions=total_sessions,
            current_session=current_session,
            project_id=project_id,
        )
        log = AuditLogEntry(
            entity_name="appointments",
            entity_id=appointment.id,
            action="create appointment",
            actor_id=data.actor_id,
            actor_type=actor_type,
            changes={
                "initial_state_must_important_info": {
                    "appointment_on_calendar_of": str(data.user_id),
                    "appointment_type": data.appointment_type.value,
                    "client_info": {
                        "vip_client_id": (
                            str(data.client_info.vip_client_id)
                            if data.client_info.vip_client_id
                            else None
                        ),
                        "name": data.client_info.name,
                        "email": data.client_info.email,
                        "phone": data.client_info.phone,
                    },
                    "start_at": data.start_at.isoformat(),
                    "end_at": data.end_at.isoformat(),
                    "referral_code": (
                        str(data.referral_code) if data.referral_code else None
                    ),
                    "project_id": (
                        str(appointment.project_id) if appointment.project_id else None
                    ),
                    "current_session": appointment.current_session,
                    "total_sessions": appointment.total_sessions,
                }
            },
            performed_at=datetime.now(timezone.utc),
        )

        return appointment, log

    def _resolve_appointment_project(
        self, project_id: UUID | None, total_sessions: int | None
    ) -> tuple[UUID | None, int | None, int | None]:
        if project_id is None:
            if total_sessions is not None and total_sessions > 1:
                project_id = uuid4()
                current_session = 1
                return project_id, current_session, total_sessions

            return None, None, total_sessions

        appointments_in_project = self.read_uow.appointments.find_many_by_project_id(project_id)
        if not appointments_in_project:
            raise AppointmentProjectNotFoundError()

        next_project_session = self.project_policy.resolve_next_session(appointments_in_project)

        if total_sessions is not None and total_sessions != next_project_session.total_sessions:
            raise TotalSessionsMustMatchProjectError()

        return (
            project_id,
            next_project_session.current_session,
            next_project_session.total_sessions,
        )

    async def _save_appointment(self, data: CreateAppointmentInput) -> Appointment:
        appointment, log = self._make_appointment(data)

        self.write_uow.appointments.create(appointment)
        self.write_uow.audit_logs.create(log)

        await self.integration_bus.publish(
            appointment.create_appointment_request(),
            uow=self.read_uow,
        )

        return appointment

    def __can_ignore_booking_window(self, *, user_id: UUID | None, calendar_user: UUID) -> bool:
        if user_id is None:
            return False

        user = self.read_uow.users.find_by_id(user_id)

        if user is None:
            return False

        if user.is_admin:
            return True

        return user.id == calendar_user
