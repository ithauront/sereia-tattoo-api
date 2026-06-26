from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

import pytest

from app.domain.studio.appointments.entities.calendar_settings import CalendarSettings
from tests.fakes.fake_calendar_settings_repository import FakeCalendarSettingsRepository
from tests.fakes.fake_users_repository import FakeUsersRepository


@pytest.fixture
def calendar_settings_repo():
    return FakeCalendarSettingsRepository()


@pytest.fixture
def users_repo():
    return FakeUsersRepository()


def test_create_and_find_by_user_id(
    make_calendar_settings, make_user, users_repo, calendar_settings_repo
):
    user = make_user()
    users_repo.create(user)

    calendar = make_calendar_settings(user_id=user.id)
    calendar_settings_repo.create(calendar)

    found = calendar_settings_repo.find_by_user_id(user.id)

    assert found is not None
    assert found.user_id == user.id
    assert found.booking_window_until == calendar.booking_window_until


def test_calendar_not_found_returns_none(
    make_calendar_settings, make_user, users_repo, calendar_settings_repo
):
    user = make_user()
    users_repo.create(user)

    calendar = make_calendar_settings(user_id=user.id)
    calendar_settings_repo.create(calendar)

    found = calendar_settings_repo.find_by_user_id(uuid4())

    assert found is None


def test_exists_by_user_id(make_calendar_settings, make_user, users_repo, calendar_settings_repo):
    user = make_user()
    users_repo.create(user)

    calendar = make_calendar_settings(user_id=user.id)
    calendar_settings_repo.create(calendar)

    exists = calendar_settings_repo.exists_by_user_id(user.id)
    do_not_exists = calendar_settings_repo.exists_by_user_id(uuid4())

    assert exists is True
    assert do_not_exists is False


def test_update(
    make_calendar_settings, make_user, users_repo, calendar_settings_repo, make_working_period
):
    user = make_user()
    users_repo.create(user)

    old_working_periods = [
        make_working_period(weekday=i, start_at=time(8, 0), end_at=time(12, 0)) for i in range(7)
    ]
    calendar: CalendarSettings = make_calendar_settings(
        user_id=user.id, working_periods=old_working_periods
    )
    calendar_settings_repo.create(calendar)

    old_entry = calendar_settings_repo.find_by_user_id(user.id)
    assert old_entry.working_periods == old_working_periods

    new_working_periods = [
        make_working_period(weekday=i, start_at=time(13, 0), end_at=time(20, 0)) for i in range(7)
    ]

    calendar.replace_working_periods(working_periods=new_working_periods)
    calendar_settings_repo.update(calendar)

    updated_entry = calendar_settings_repo.find_by_user_id(user.id)

    assert updated_entry.working_periods == new_working_periods
    assert calendar is updated_entry
    assert len(calendar_settings_repo._calendar_settings) == 1


def test_update_nonexistent_user_does_nothing(make_calendar_settings, calendar_settings_repo):
    calendar = make_calendar_settings()

    calendar_settings_repo.update(calendar)
    found = calendar_settings_repo.find_by_user_id(calendar.user_id)

    assert found is None


def test_find_by_user_id_returns_none_when_repository_is_empty(
    calendar_settings_repo,
):
    calendar = calendar_settings_repo.find_by_user_id(uuid4())
    assert calendar is None


def test_update_only_changes_target_user(
    make_calendar_settings,
    make_user,
    users_repo,
    calendar_settings_repo,
):
    user_1 = make_user()
    user_2 = make_user()

    users_repo.create(user_1)
    users_repo.create(user_2)

    calendar_1 = make_calendar_settings(user_id=user_1.id)
    calendar_2 = make_calendar_settings(user_id=user_2.id)

    calendar_settings_repo.create(calendar_1)
    calendar_settings_repo.create(calendar_2)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    next_month = (base_now + timedelta(days=30)).date()

    calendar_1.booking_window_until = next_month
    calendar_settings_repo.update(calendar_1)

    found_1 = calendar_settings_repo.find_by_user_id(user_1.id)
    found_2 = calendar_settings_repo.find_by_user_id(user_2.id)

    assert found_1.booking_window_until == next_month
    assert found_2.booking_window_until == calendar_2.booking_window_until
