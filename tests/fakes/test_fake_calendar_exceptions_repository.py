from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import between

from tests.fakes.fake_calendar_exceptions_repository import FakeCalendarExceptionsRepository


@pytest.fixture
def calendar_exceptions_repo():
    return FakeCalendarExceptionsRepository()


def test_create_and_find_by_id(make_calendar_exception, calendar_exceptions_repo):
    calendar_exception = make_calendar_exception()

    calendar_exceptions_repo.create(calendar_exception)

    found = calendar_exceptions_repo.find_by_id(calendar_exception.id)

    assert found is not None
    assert found.calendar_of_user == calendar_exception.calendar_of_user


def test_not_found(make_calendar_exception, calendar_exceptions_repo):
    calendar_exception = make_calendar_exception()
    # we do not persist for this test
    found = calendar_exceptions_repo.find_by_id(calendar_exception.id)

    assert found is None


def test_find_by_id_returns_none_when_repository_is_empty(calendar_exceptions_repo):
    calendar_exception = calendar_exceptions_repo.find_by_id(uuid4())
    assert calendar_exception is None


def test_update(make_calendar_exception, calendar_exceptions_repo):
    calendar_exception = make_calendar_exception(start_at=datetime(2026, 1, 1, 10, 0))

    calendar_exceptions_repo.create(calendar_exception)

    calendar_exception.start_at = datetime(2026, 1, 1, 11, 0)

    calendar_exceptions_repo.update(calendar_exception)

    found = calendar_exceptions_repo.find_by_id(calendar_exception.id)

    assert found.start_at == datetime(2026, 1, 1, 11, 0)


def test_update_non_existent_calendar_exception_does_nothing(
    make_calendar_exception, calendar_exceptions_repo
):
    calendar_exception = make_calendar_exception(start_at=datetime(2026, 1, 1, 10, 0))

    # we do not persist for this test

    calendar_exception.start_at = datetime(2026, 1, 1, 11, 0)

    calendar_exceptions_repo.update(calendar_exception)

    found = calendar_exceptions_repo.find_by_id(calendar_exception.id)

    assert found is None


def test_update_only_changes_target_calendar_exception(
    make_calendar_exception, calendar_exceptions_repo
):
    calendar_exception_1 = make_calendar_exception(start_at=datetime(2026, 1, 1, 10, 0))
    calendar_exception_2 = make_calendar_exception(start_at=datetime(2026, 1, 1, 10, 0))

    calendar_exceptions_repo.create(calendar_exception_1)
    calendar_exceptions_repo.create(calendar_exception_2)

    calendar_exception_1.start_at = datetime(2026, 1, 1, 11, 0)

    calendar_exceptions_repo.update(calendar_exception_1)

    found_1 = calendar_exceptions_repo.find_by_id(calendar_exception_1.id)
    found_2 = calendar_exceptions_repo.find_by_id(calendar_exception_2.id)

    assert found_1.start_at == datetime(2026, 1, 1, 11, 0)
    assert found_2.start_at == datetime(2026, 1, 1, 10, 0)


def test_find_between(make_calendar_exception, calendar_exceptions_repo):
    calendar_exception = make_calendar_exception(
        start_at=datetime(2026, 1, 1, 10, 0), end_at=datetime(2026, 1, 1, 13, 0)
    )
    calendar_exceptions_repo.create(calendar_exception)

    between
