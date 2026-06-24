from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.studio.appointments.entities.calendar_settings import CalendarSettings


class CalendarSettingsRepository(ABC):
    @abstractmethod
    def create(self, calendar_settings: CalendarSettings) -> None: ...

    @abstractmethod
    def find_by_user_id(self, user_id: UUID) -> Optional[CalendarSettings]: ...

    @abstractmethod
    def update(self, calendar_settings: CalendarSettings) -> None: ...

    @abstractmethod
    def exists_by_user_id(
        self,
        user_id: UUID,
    ) -> bool: ...
