from typing import Optional
from uuid import UUID

from app.application.studio.repositories.calendar_settings_repository import CalendarSettingsRepository
from app.domain.studio.appointments.entities.calendar_settings import CalendarSettings
from app.domain.studio.appointments.entities.working_period import WorkingPeriod
from app.infrastructure.sqlalchemy.models.calendar_settings import CalendarSettingsModel
from app.infrastructure.sqlalchemy.models.working_period import WorkingPeriodModel
from sqlalchemy import exists, select
from sqlalchemy.orm import Session


# TODO: fazer todos os metodos e fazer testes fazer fake e teste tambem
class SQLAlchemyCalendarSettingsRepository(CalendarSettingsRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, calendar_settings: CalendarSettings) -> None:
        orm_calendar_settings = self._calendar_settings_mapper_to_model(calendar_settings)

        self.session.add(orm_calendar_settings)
        self.session.flush()

    def find_by_user_id(self, user_id: UUID) -> Optional[CalendarSettings]:
        calendar_in_question = select(CalendarSettingsModel).where(
            CalendarSettingsModel.user_id == user_id
        )
        orm_calendar_settings = self.session.scalar(calendar_in_question)

        if orm_calendar_settings is None:
            return None

        return self._calendar_settings_mapper_to_entity(orm_calendar_settings)

    def update(self, calendar_settings: CalendarSettings) -> None:
        calendar_in_question = select(CalendarSettingsModel).where(
            CalendarSettingsModel.user_id == calendar_settings.user_id
        )

        orm_calendar_settings = self.session.scalar(calendar_in_question)

        if orm_calendar_settings is None:
            return None

        orm_calendar_settings.booking_window_until = calendar_settings.booking_window_until
        orm_calendar_settings.working_periods.clear()
        orm_calendar_settings.working_periods.extend(
            [
                self._working_period_mapper_to_model(period)
                for period in calendar_settings.working_periods
            ]
        )
        orm_calendar_settings.updated_at = calendar_settings.updated_at

        self.session.flush()

    def exists_by_user_id(self, user_id: UUID) -> bool:
        calendar = select(exists().where(CalendarSettingsModel.user_id == user_id))

        return self.session.scalar(calendar) or False

    def _calendar_settings_mapper_to_model(
        self, calendar_settings: CalendarSettings
    ) -> CalendarSettingsModel:
        orm_calendar_settings = CalendarSettingsModel(
            user_id=calendar_settings.user_id,
            booking_window_until=calendar_settings.booking_window_until,
            created_at=calendar_settings.created_at,
            updated_at=calendar_settings.updated_at,
        )
        orm_calendar_settings.working_periods = [
            self._working_period_mapper_to_model(period) for period in calendar_settings.working_periods
        ]

        return orm_calendar_settings

    def _calendar_settings_mapper_to_entity(
        self, orm_calendar_settings: CalendarSettingsModel
    ) -> CalendarSettings:
        working_periods = [
            WorkingPeriod(
                id=period.id,
                weekday=period.weekday,
                start_at=period.start_at,
                end_at=period.end_at,
                created_at=period.created_at,
                updated_at=period.updated_at,
            )
            for period in orm_calendar_settings.working_periods
        ]

        return CalendarSettings(
            user_id=orm_calendar_settings.user_id,
            booking_window_until=orm_calendar_settings.booking_window_until,
            working_periods=working_periods,
            created_at=orm_calendar_settings.created_at,
            updated_at=orm_calendar_settings.updated_at,
        )

    def _working_period_mapper_to_entity(self, orm_working_period: WorkingPeriodModel) -> WorkingPeriod:
        return WorkingPeriod(
            id=orm_working_period.id,
            weekday=orm_working_period.weekday,
            start_at=orm_working_period.start_at,
            end_at=orm_working_period.end_at,
            created_at=orm_working_period.created_at,
            updated_at=orm_working_period.updated_at,
        )

    def _working_period_mapper_to_model(self, working_period: WorkingPeriod) -> WorkingPeriodModel:
        return WorkingPeriodModel(
            id=working_period.id,
            weekday=working_period.weekday,
            start_at=working_period.start_at,
            end_at=working_period.end_at,
            created_at=working_period.created_at,
            updated_at=working_period.updated_at,
        )
