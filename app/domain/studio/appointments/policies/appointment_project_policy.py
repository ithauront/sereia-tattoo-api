from dataclasses import dataclass
from typing import Sequence

from app.core.exceptions.appointments import (
    AppointmentProjectStateError,
    TotalSessionsExceededError,
)
from app.core.types.appointment_enums import AppointmentStatus
from app.domain.studio.appointments.entities.appointment import Appointment


@dataclass(frozen=True)
class NextProjectSession:
    current_session: int
    total_sessions: int


class AppointmentProjectPolicy:
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
                return NextProjectSession(
                    current_session=session_number,
                    total_sessions=project_total,
                )

        next_session = highest_existing_session + 1
        if next_session > project_total:
            raise TotalSessionsExceededError()

        return NextProjectSession(
            current_session=next_session,
            total_sessions=project_total,
        )
