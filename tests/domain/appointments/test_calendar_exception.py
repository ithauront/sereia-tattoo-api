from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.exceptions.calendar import (
    CalendarExceptionMustHaveRealisticTimeAndDateError,
    InvalidReasonError,
)
from app.core.exceptions.validation import ValidationError
from app.core.types.calendar_enums import CalendarExceptionType
from app.domain.studio.appointments.entities.calendar_exception import CalendarException


def test_calendar_exception_type_not_valid():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    with pytest.raises(ValidationError) as exc:
        CalendarException.create(
            start_at=now_plus_2,
            end_at=now_plus_4,
            calendar_of_user=uuid4(),
            created_by=uuid4(),
            exception_type="invalid_type",  # type: ignore
            reason="test reason",
        )

    assert "Invalid value" in str(exc.value)


def test_end_cannot_by_less_than_start_on_create():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    with pytest.raises(CalendarExceptionMustHaveRealisticTimeAndDateError):
        CalendarException.create(
            start_at=now_plus_4,
            end_at=now_plus_2,
            calendar_of_user=uuid4(),
            created_by=uuid4(),
            exception_type=CalendarExceptionType.BLOCK,
            reason="test reason",
        )


def test_start_cannot_be_before_now_on_create():
    now = datetime.now(timezone.utc)
    now_minus_2 = now - timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    with pytest.raises(CalendarExceptionMustHaveRealisticTimeAndDateError):
        CalendarException.create(
            start_at=now_minus_2,
            end_at=now_plus_4,
            calendar_of_user=uuid4(),
            created_by=uuid4(),
            exception_type=CalendarExceptionType.BLOCK,
            reason="test reason",
        )


def test_end_cannot_by_less_than_start_on_reschedule():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    with pytest.raises(CalendarExceptionMustHaveRealisticTimeAndDateError):
        calendar_exception.reschedule(start_at=now_plus_4, end_at=now_plus_2)


def test_start_cannot_be_before_now_on_reschedule():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_minus_2 = now - timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    with pytest.raises(CalendarExceptionMustHaveRealisticTimeAndDateError):
        calendar_exception.reschedule(start_at=now_minus_2, end_at=now_plus_4)


def test_update_canot_have_empty_reason():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    with pytest.raises(InvalidReasonError):
        calendar_exception.update_reason(reason="  ")


def test_update_canot_have_none_reason():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    with pytest.raises(InvalidReasonError):
        calendar_exception.update_reason(reason=None)  # type: ignore


def test_change_type_true():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    it_changed = calendar_exception.change_type(new_exception_type=CalendarExceptionType.ALLOW)

    assert it_changed is True
    assert calendar_exception.exception_type == CalendarExceptionType.ALLOW


def test_change_type_false():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    it_changed = calendar_exception.change_type(new_exception_type=CalendarExceptionType.BLOCK)

    assert it_changed is False
    assert calendar_exception.exception_type == CalendarExceptionType.BLOCK


def test_overlap_true():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    overlap = calendar_exception.overlaps(start_at=now, end_at=now + timedelta(hours=3))
    assert overlap is True


def test_overlap_false():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    overlap = calendar_exception.overlaps(
        start_at=now + timedelta(hours=5), end_at=now + timedelta(hours=5)
    )
    assert overlap is False


def test_overlap_touching_return_false():
    now = datetime.now(timezone.utc)
    now_plus_2 = now + timedelta(hours=2)
    now_plus_4 = now + timedelta(hours=4)

    calendar_exception = CalendarException.create(
        start_at=now_plus_2,
        end_at=now_plus_4,
        calendar_of_user=uuid4(),
        created_by=uuid4(),
        exception_type=CalendarExceptionType.BLOCK,
        reason="test reason",
    )

    overlap = calendar_exception.overlaps(start_at=now_plus_4, end_at=now_plus_2)
    assert overlap is False
