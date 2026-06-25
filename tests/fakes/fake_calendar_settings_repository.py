from typing import List, Optional
from uuid import UUID

from app.application.studio.repositories.calendar_settings_repository import CalendarSettingsRepository
from app.domain.studio.appointments.entities.calendar_settings import CalendarSettings


class FakeCalendarSettingsRepository(CalendarSettingsRepository):
    def __init__(self):
        self._calendar_settings: List[CalendarSettings] = []

    def create(self, calendar_settings: CalendarSettings) -> None:
        self._calendar_settings.append(calendar_settings)

    def find_by_user_id(self, user_id: UUID) -> Optional[CalendarSettings]:
        for calendar in self._calendar_settings:
            if calendar.user_id == user_id:
                return calendar

        return None

    def update(self, calendar_settings: CalendarSettings) -> None:
        for index, calendar_setting_in_question in enumerate(self._calendar_settings):
            if calendar_setting_in_question.user_id == calendar_settings.user_id:
                self._calendar_settings[index] = calendar_settings
                return

    def exists_by_user_id(self, user_id: UUID) -> bool:
        for calendar in self._calendar_settings:
            if calendar.user_id == user_id:
                return True

        return False
