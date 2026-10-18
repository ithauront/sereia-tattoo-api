from dataclasses import dataclass
from typing import Sequence

from app.core.exceptions.appointments import (
    AppointmentProjectStateError,
    ProjectSessionAlreadyOccupiedError,
    ProjectSessionMustBeRescheduledError,
    TotalSessionsExceededError,
)
from app.core.types.appointment_enums import AppointmentStatus
from app.domain.studio.appointments.entities.appointment import Appointment


@dataclass(frozen=True)
class NextProjectSession:
    current_session: int
    total_sessions: int


class AppointmentProjectPolicy:
    def ensure_can_replace_session(
        self, *, appointment: Appointment, appointments: Sequence[Appointment]
    ) -> None:
        if (
            appointment.project_id is None
            or appointment.current_session is None
            or appointment.total_sessions is None
        ):
            raise AppointmentProjectStateError()

        if not any(item.id == appointment.id for item in appointments):
            raise AppointmentProjectStateError()

        for project_appointment in appointments:
            if (
                project_appointment.project_id != appointment.project_id
                or project_appointment.total_sessions != appointment.total_sessions
                or project_appointment.current_session is None
            ):
                raise AppointmentProjectStateError()

        for project_appointment in appointments:
            if (
                project_appointment.id != appointment.id
                and project_appointment.current_session == appointment.current_session
                and project_appointment.status != AppointmentStatus.CANCELED
            ):
                raise ProjectSessionAlreadyOccupiedError()

    def resolve_next_session(self, appointments: Sequence[Appointment]) -> NextProjectSession:
        if not appointments:
            raise AppointmentProjectStateError()

        project_total = appointments[0].total_sessions
        if project_total is None:
            raise AppointmentProjectStateError()

        existing_session_numbers: set[int] = set()
        non_canceled_session_numbers: set[int] = set()

        for appointment in appointments:
            if appointment.current_session is None or appointment.total_sessions != project_total:
                raise AppointmentProjectStateError()

            session_number = appointment.current_session
            existing_session_numbers.add(session_number)

            if appointment.status == AppointmentStatus.CANCELED:
                continue

            if session_number in non_canceled_session_numbers:
                raise AppointmentProjectStateError()

            non_canceled_session_numbers.add(session_number)

        highest_existing_session = max(existing_session_numbers)
        for session_number in range(1, highest_existing_session + 1):
            if session_number not in existing_session_numbers:
                raise AppointmentProjectStateError()

            if session_number not in non_canceled_session_numbers:
                raise ProjectSessionMustBeRescheduledError()

        next_session = highest_existing_session + 1
        if next_session > project_total:
            raise TotalSessionsExceededError()

        return NextProjectSession(
            current_session=next_session,
            total_sessions=project_total,
        )
