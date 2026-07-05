from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.application.studio.repositories.calendar_exceptions_repository import (
    CalendarExceptionsRepository,
)
from app.domain.studio.appointments.entities.calendar_exception import CalendarException
from app.infrastructure.sqlalchemy.models.calendar_exceptions import CalendarExceptionsModel
from sqlalchemy import select
from sqlalchemy.orm import Session


# TODO: verificar a questão dos utc. talvez no mapper colocar todos os retornos para ser utc aware em todos os repositorios
class SQLAlchemyCalendarExceptionsRepository(CalendarExceptionsRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, calendar_exception: CalendarException) -> None:
        orm_calendar_exception = self._to_model(calendar_exception)

        self.session.add(orm_calendar_exception)
        self.session.flush()

    def update(self, calendar_exception: CalendarException) -> None:
        calendar_exception_in_question = select(CalendarExceptionsModel).where(
            CalendarExceptionsModel.id == calendar_exception.id
        )

        orm_calendar_exception = self.session.scalar(calendar_exception_in_question)

        if orm_calendar_exception is None:
            return None

        orm_calendar_exception.start_at = calendar_exception.start_at
        orm_calendar_exception.end_at = calendar_exception.end_at
        orm_calendar_exception.exception_type = calendar_exception.exception_type
        orm_calendar_exception.reason = calendar_exception.reason
        orm_calendar_exception.updated_at = calendar_exception.updated_at

        self.session.flush()

    def find_by_id(self, calendar_exception_id: UUID) -> Optional[CalendarException]:
        calendar_exception_in_question = select(CalendarExceptionsModel).where(
            CalendarExceptionsModel.id == calendar_exception_id
        )

        orm_calendar_exception = self.session.scalar(calendar_exception_in_question)

        if orm_calendar_exception is None:
            return

        return self._to_entity(orm_calendar_exception)

    def find_between(
        self, *, user_id: UUID, start_at: datetime, end_at: datetime
    ) -> List[CalendarException]:
        calendar_exceptions_in_question = (
            select(CalendarExceptionsModel)
            .where(
                CalendarExceptionsModel.calendar_of_user == user_id,
                CalendarExceptionsModel.start_at >= start_at,
                CalendarExceptionsModel.end_at <= end_at,
            )
            .order_by(CalendarExceptionsModel.start_at.asc(), CalendarExceptionsModel.end_at.asc())
        )
        orm_calendar_exception = self.session.scalars(calendar_exceptions_in_question)

        return [self._to_entity(exception) for exception in orm_calendar_exception]

    def find_overlap(
        self, *, user_id: UUID, start_at: datetime, end_at: datetime
    ) -> List[CalendarException]:
        calendar_exceptions_in_question = (
            select(CalendarExceptionsModel)
            .where(
                CalendarExceptionsModel.calendar_of_user == user_id,
                CalendarExceptionsModel.start_at < end_at,
                CalendarExceptionsModel.end_at > start_at,
            )
            .order_by(CalendarExceptionsModel.start_at.asc(), CalendarExceptionsModel.end_at.asc())
        )
        orm_calendar_exception = self.session.scalars(calendar_exceptions_in_question)

        return [self._to_entity(exception) for exception in orm_calendar_exception]

    def delete(self, calendar_exception_id: UUID) -> None:
        calendar_exception_in_question = select(CalendarExceptionsModel).where(
            CalendarExceptionsModel.id == calendar_exception_id
        )

        orm_calendar_exception = self.session.scalar(calendar_exception_in_question)

        if orm_calendar_exception is None:
            return

        self.session.delete(orm_calendar_exception)

        self.session.flush()

    def _to_model(self, calendar_exception: CalendarException) -> CalendarExceptionsModel:

        return CalendarExceptionsModel(
            id=calendar_exception.id,
            calendar_of_user=calendar_exception.calendar_of_user,
            start_at=calendar_exception.start_at,
            end_at=calendar_exception.end_at,
            exception_type=calendar_exception.exception_type,
            reason=calendar_exception.reason,
            created_by=calendar_exception.created_by,
            created_at=calendar_exception.created_at,
            updated_at=calendar_exception.updated_at,
        )

    def _to_entity(self, orm_calendar_exception: CalendarExceptionsModel) -> CalendarException:

        return CalendarException(
            id=orm_calendar_exception.id,
            calendar_of_user=orm_calendar_exception.calendar_of_user,
            start_at=orm_calendar_exception.start_at,
            end_at=orm_calendar_exception.end_at,
            exception_type=orm_calendar_exception.exception_type,
            reason=orm_calendar_exception.reason,
            created_by=orm_calendar_exception.created_by,
            created_at=orm_calendar_exception.created_at,
            updated_at=orm_calendar_exception.updated_at,
        )
