from datetime import time
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.infrastructure.sqlalchemy.repositories.calendar_settings_repository_sqlalchemy import (
    SQLAlchemyCalendarSettingsRepository,
)
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)


def test_create_and_find_by_id(
    sqlalchemy_calendar_settings_repo: SQLAlchemyCalendarSettingsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_settings,
):
    user = make_user()

    sqlalchemy_users_repo.create(user)

    calendar = make_calendar_settings(user_id=user.id)
    sqlalchemy_calendar_settings_repo.create(calendar)

    found = sqlalchemy_calendar_settings_repo.find_by_user_id(user.id)

    assert found is not None
    assert found.user_id == user.id
    assert found.user_id == calendar.user_id


def test_user_cannot_have_more_than_one_calendar(
    sqlalchemy_calendar_settings_repo: SQLAlchemyCalendarSettingsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_settings,
):
    user = make_user()

    sqlalchemy_users_repo.create(user)

    first_calendar = make_calendar_settings(user_id=user.id)
    sqlalchemy_calendar_settings_repo.create(first_calendar)

    second_calendar = make_calendar_settings(user_id=user.id)

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_settings_repo.create(second_calendar)


def test_calendar_requires_existing_user_fk(
    sqlalchemy_calendar_settings_repo,
    make_calendar_settings,
):
    calendar = make_calendar_settings(user_id=uuid4())

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_settings_repo.create(calendar)


def test_working_period_end_must_be_after_start(
    sqlalchemy_calendar_settings_repo,
    sqlalchemy_users_repo,
    make_user,
    make_calendar_settings,
    make_working_period,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar = make_calendar_settings(user_id=user.id)
    calendar.working_periods = [
        make_working_period(
            weekday=1,
            start_at=time(12),
            end_at=time(10),
        )
    ]

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_settings_repo.create(calendar)


def test_calendar_returns_working_periods(
    sqlalchemy_calendar_settings_repo,
    sqlalchemy_users_repo,
    make_user,
    make_calendar_settings,
    make_working_period,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar = make_calendar_settings(user_id=user.id)
    calendar.working_periods = [
        make_working_period(weekday=1, start_at=time(8), end_at=time(12)),
    ]

    sqlalchemy_calendar_settings_repo.create(calendar)

    found = sqlalchemy_calendar_settings_repo.find_by_user_id(user.id)

    assert len(found.working_periods) == 1
    assert found.working_periods[0].weekday == 1


def test_booking_window_cannot_be_null(
    sqlalchemy_calendar_settings_repo,
    sqlalchemy_users_repo,
    make_user,
    make_calendar_settings,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar = make_calendar_settings(user_id=user.id, booking_window_until=None)

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_settings_repo.create(calendar)


def test_orphan_removal_persists_in_db(
    sqlalchemy_calendar_settings_repo,
    sqlalchemy_users_repo,
    make_user,
    make_calendar_settings,
    make_working_period,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar = make_calendar_settings(user_id=user.id)

    period = make_working_period()
    calendar.working_periods = [period]

    sqlalchemy_calendar_settings_repo.create(calendar)

    calendar.remove_working_period(period.id)
    sqlalchemy_calendar_settings_repo.update(calendar)

    found = sqlalchemy_calendar_settings_repo.find_by_user_id(user.id)

    assert len(found.working_periods) == 0
