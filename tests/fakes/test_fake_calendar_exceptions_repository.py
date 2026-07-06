from datetime import datetime
from uuid import uuid4

import pytest

from tests.fakes.fake_calendar_exceptions_repository import FakeCalendarExceptionsRepository
from tests.fakes.fake_users_repository import FakeUsersRepository


@pytest.fixture
def calendar_exceptions_repo():
    return FakeCalendarExceptionsRepository()


@pytest.fixture
def users_repo():
    return FakeUsersRepository()


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


def test_find_between(make_calendar_exception, calendar_exceptions_repo, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    all_in_between = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 10, 0),
        end_at=datetime(2026, 1, 1, 13, 0),
    )
    calendar_exceptions_repo.create(all_in_between)

    same_start_end_in_between = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 9, 0),
        end_at=datetime(2026, 1, 1, 13, 0),
    )
    calendar_exceptions_repo.create(same_start_end_in_between)

    start_in_between_same_end = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 10, 0),
        end_at=datetime(2026, 1, 1, 15, 0),
    )
    calendar_exceptions_repo.create(start_in_between_same_end)

    start_before = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 8, 0),
        end_at=datetime(2026, 1, 1, 14, 0),
    )
    calendar_exceptions_repo.create(start_before)

    end_after = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 10, 0),
        end_at=datetime(2026, 1, 1, 17, 0),
    )
    calendar_exceptions_repo.create(end_after)

    between = calendar_exceptions_repo.find_between(
        user_id=user.id,
        start_at=datetime(2026, 1, 1, 9, 0),
        end_at=datetime(2026, 1, 1, 15, 0),
    )

    assert between is not None
    assert len(between) == 3
    assert sorted(between, key=lambda exception: (exception.start_at, exception.end_at)) == between


def test_find_overlap(make_calendar_exception, calendar_exceptions_repo, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    start_before_end_in_range = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 8, 0),
        end_at=datetime(2026, 1, 1, 14, 0),
    )

    calendar_exceptions_repo.create(start_before_end_in_range)

    same_start_end_in_between = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 9, 0),
        end_at=datetime(2026, 1, 1, 13, 0),
    )

    calendar_exceptions_repo.create(same_start_end_in_between)

    all_in_between = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 10, 0),
        end_at=datetime(2026, 1, 1, 13, 0),
    )
    calendar_exceptions_repo.create(all_in_between)

    start_in_between_same_end = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 10, 0),
        end_at=datetime(2026, 1, 1, 15, 0),
    )
    calendar_exceptions_repo.create(start_in_between_same_end)

    start_in_range_end_after = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 10, 0),
        end_at=datetime(2026, 1, 1, 17, 0),
    )
    calendar_exceptions_repo.create(start_in_range_end_after)

    does_not_overlap_after = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 15, 0),
        end_at=datetime(2026, 1, 1, 17, 0),
    )
    calendar_exceptions_repo.create(does_not_overlap_after)

    does_not_overlap_before = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 6, 0),
        end_at=datetime(2026, 1, 1, 9, 0),
    )
    calendar_exceptions_repo.create(does_not_overlap_before)

    does_not_overlap_and_dont_touch = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 6, 0),
        end_at=datetime(2026, 1, 1, 8, 0),
    )
    calendar_exceptions_repo.create(does_not_overlap_and_dont_touch)

    overlap = calendar_exceptions_repo.find_overlap(
        user_id=user.id,
        start_at=datetime(2026, 1, 1, 9, 0),
        end_at=datetime(2026, 1, 1, 15, 0),
    )

    assert overlap is not None
    assert len(overlap) == 5
    assert sorted(overlap, key=lambda exception: (exception.start_at, exception.end_at)) == overlap


def test_find_delete(make_calendar_exception, calendar_exceptions_repo, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    calendar_1 = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 8, 0),
        end_at=datetime(2026, 1, 1, 14, 0),
    )

    calendar_exceptions_repo.create(calendar_1)

    calendar_2 = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 9, 0),
        end_at=datetime(2026, 1, 1, 13, 0),
    )

    calendar_exceptions_repo.create(calendar_2)

    founds = calendar_exceptions_repo.find_between(
        user_id=user.id, start_at=datetime(2026, 1, 1, 8, 0), end_at=datetime(2026, 1, 1, 14, 0)
    )
    assert len(founds) == 2

    calendar_exceptions_repo.delete(calendar_1.id)
    founds_after_delete = calendar_exceptions_repo.find_between(
        user_id=user.id, start_at=datetime(2026, 1, 1, 8, 0), end_at=datetime(2026, 1, 1, 14, 0)
    )

    try_to_find_deleted = calendar_exceptions_repo.find_by_id(calendar_1.id)

    assert try_to_find_deleted is None

    assert len(founds_after_delete) == 1
    assert founds_after_delete[0].id == calendar_2.id
