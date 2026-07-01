from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.studio.appointments.entities.calendar_exception import CalendarException


class CalendarExceptionsRepository(ABC):
    @abstractmethod
    def create(self, calendar_exception: CalendarException) -> None: ...

    @abstractmethod
    def update(self, calendar_exception: CalendarException) -> None: ...

    @abstractmethod
    def find_by_id(self, calendar_exception_id: UUID) -> Optional[CalendarException]: ...

    """
        Return exceptions fully contained within the given interval.
    """

    @abstractmethod
    def find_between(
        self,
        *,
        user_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> List[CalendarException]: ...

    """
        Return exceptions that overlap any portion of the given interval.
    """

    @abstractmethod
    def find_overlap(
        self,
        *,
        user_id: UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> List[CalendarException]: ...

    @abstractmethod
    def delete(self, calendar_exception_id: UUID) -> None: ...
