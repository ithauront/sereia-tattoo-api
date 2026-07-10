from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.studio.appointments.entities.calendar_exception import CalendarException
from app.infrastructure.sqlalchemy.repositories.calendar_exceptions_repository_sqlalchemy import (
    SQLAlchemyCalendarExceptionsRepository,
)
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)


def test_create_and_find_by_id(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar_exception = make_calendar_exception(calendar_of_user=user.id, created_by=user.id)
    sqlalchemy_calendar_exceptions_repo.create(calendar_exception)

    found = sqlalchemy_calendar_exceptions_repo.find_by_id(calendar_exception.id)

    assert found is not None
    assert found.id == calendar_exception.id


def test_find_between_is_subset_of_find_overlap(
    sqlalchemy_calendar_exceptions_repo,
    sqlalchemy_users_repo,
    make_user,
    make_calendar_exception,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    for i in range(5):
        calendar_exception = make_calendar_exception(
            calendar_of_user=user.id,
            start_at=datetime(2026, 1, 1, i, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 1, 1, i + 1, 0, tzinfo=timezone.utc),
            created_by=user.id,
        )
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)

    start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    between = sqlalchemy_calendar_exceptions_repo.find_between(
        user_id=user.id, start_at=start, end_at=end
    )
    overlap = sqlalchemy_calendar_exceptions_repo.find_overlap(
        user_id=user.id, start_at=start, end_at=end
    )

    between_ids = {exception.id for exception in between}
    overlap_ids = {exception.id for exception in overlap}

    assert between_ids.issubset(overlap_ids)


def test_end_must_be_after_start(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar_exception = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        created_by=user.id,
    )

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)


def test_start_not_nullable(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar_exception = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=None,
        end_at=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        created_by=user.id,
    )

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)


def test_end_not_nullable(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar_exception = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        end_at=None,
        created_by=user.id,
    )

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)


def test_created_by_fk_must_exist(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar_exception = make_calendar_exception(calendar_of_user=user.id, created_by=uuid4())

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)


def test_calendar_of_user_fk_must_exist(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar_exception = make_calendar_exception(calendar_of_user=uuid4(), created_by=user.id)

    with pytest.raises(IntegrityError):
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)


def test_users_have_own_exceptions(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):

    user_1 = make_user(email="jhon@doe.com", username="jhondoe")
    sqlalchemy_users_repo.create(user_1)

    calendar_exception_user_1 = make_calendar_exception(
        calendar_of_user=user_1.id,
        start_at=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
        created_by=user_1.id,
        reason="user 1",
    )

    sqlalchemy_calendar_exceptions_repo.create(calendar_exception_user_1)

    user_2 = make_user(email="jane@doe.com", username="janedoe")
    sqlalchemy_users_repo.create(user_2)

    calendar_exception_user_2 = make_calendar_exception(
        calendar_of_user=user_2.id,
        created_by=user_2.id,
        reason="user 2",
    )

    sqlalchemy_calendar_exceptions_repo.create(calendar_exception_user_2)

    found_exception_of_user_1 = sqlalchemy_calendar_exceptions_repo.find_between(
        user_id=user_1.id,
        start_at=datetime(2026, 1, 1, 7, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert found_exception_of_user_1[0].reason == "user 1"
    assert len(found_exception_of_user_1) == 1


def test_result_came_ordered(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):

    user = make_user()
    sqlalchemy_users_repo.create(user)

    for i in range(5):
        calendar_exception = make_calendar_exception(
            calendar_of_user=user.id,
            start_at=datetime(2026, 1, 1, i, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
            created_by=user.id,
        )
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)

    founds = sqlalchemy_calendar_exceptions_repo.find_between(
        user_id=user.id,
        start_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert founds[0].start_at == datetime(2026, 1, 1, 0, 0)
    assert founds[4].start_at == datetime(2026, 1, 1, 4, 0)
    assert len(founds) == 5


def test_empty_list_for_between(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):

    user = make_user()
    sqlalchemy_users_repo.create(user)

    for i in range(5):
        calendar_exception = make_calendar_exception(
            calendar_of_user=user.id,
            start_at=datetime(2026, 1, 1, i, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
            created_by=user.id,
        )
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)

    founds = sqlalchemy_calendar_exceptions_repo.find_between(
        user_id=uuid4(),
        start_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert founds == []


def test_empty_list_for_overlap(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):

    user = make_user()
    sqlalchemy_users_repo.create(user)

    for i in range(5):
        calendar_exception = make_calendar_exception(
            calendar_of_user=user.id,
            start_at=datetime(2026, 1, 1, i, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
            created_by=user.id,
        )
        sqlalchemy_calendar_exceptions_repo.create(calendar_exception)

    founds = sqlalchemy_calendar_exceptions_repo.find_overlap(
        user_id=uuid4(),
        start_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert founds == []


def test_update_affect_query_results(
    sqlalchemy_calendar_exceptions_repo: SQLAlchemyCalendarExceptionsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
    make_calendar_exception,
):

    user = make_user()
    sqlalchemy_users_repo.create(user)

    calendar_exception_1: CalendarException = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
        created_by=user.id,
        reason="exception 1",
    )
    sqlalchemy_calendar_exceptions_repo.create(calendar_exception_1)

    calendar_exception_2 = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc),
        created_by=user.id,
        reason="exception 2",
    )
    sqlalchemy_calendar_exceptions_repo.create(calendar_exception_2)

    founds_before_update = sqlalchemy_calendar_exceptions_repo.find_between(
        user_id=user.id,
        start_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert len(founds_before_update) == 2
    assert founds_before_update[0].reason == "exception 1"

    calendar_exception_1.start_at = datetime(2026, 1, 1, 5, 0, tzinfo=timezone.utc)

    sqlalchemy_calendar_exceptions_repo.update(calendar_exception_1)

    founds_after_update = sqlalchemy_calendar_exceptions_repo.find_between(
        user_id=user.id,
        start_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert len(founds_after_update) == 2
    assert founds_after_update[0].reason == "exception 2"
