from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.application.studio.repositories.calendar_exceptions_repository import (
    CalendarExceptionsRepository,
)
from app.domain.studio.appointments.entities.calendar_exception import CalendarException


# TODO: fazer o teste desse repo
class FakeCalendarExceptionsRepository(CalendarExceptionsRepository):
    def __init__(self):
        self._calendar_exceptions: List[CalendarException] = []

    def create(self, calendar_exception: CalendarException) -> None:
        self._calendar_exceptions.append(calendar_exception)

    def update(self, calendar_exception: CalendarException) -> None:
        for index, calendar_exception_in_question in enumerate(self._calendar_exceptions):
            if calendar_exception_in_question.id == calendar_exception.id:
                self._calendar_exceptions[index] = calendar_exception
                return

    def find_by_id(self, calendar_exception_id: UUID) -> Optional[CalendarException]:
        for calendar_exception in self._calendar_exceptions:
            if calendar_exception.id == calendar_exception_id:
                return calendar_exception
        return None

    def find_between(
        self, *, user_id: UUID, start_at: datetime, end_at: datetime
    ) -> List[CalendarException]:
        return [
            exception
            for exception in self._calendar_exceptions
            if exception.calendar_of_user == user_id
            and exception.start_at >= start_at
            and exception.end_at <= end_at
        ]

    def find_overlap(
        self, *, user_id: UUID, start_at: datetime, end_at: datetime
    ) -> List[CalendarException]:
        return [
            exception
            for exception in self._calendar_exceptions
            if exception.calendar_of_user == user_id
            and exception.start_at < end_at
            and exception.end_at > start_at
        ]

    def delete(self, calendar_exception_id: UUID) -> None:
        for index, calendar_exception in enumerate(self._calendar_exceptions):
            if calendar_exception.id == calendar_exception_id:
                self._calendar_exceptions.pop(index)
                return
