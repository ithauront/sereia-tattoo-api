from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone, tzinfo
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.application.studio.use_cases.DTO.reschedule_appointment_dto import (
    RescheduleAppointmentInput,
    RescheduleAppointmentOutput,
)
from app.core.exceptions.appointments import AppointmentMustHaveRealisticTimeAndDateError
from app.core.types.appointment_enums import AppointmentStatus

START = datetime(2035, 1, 10, 12, tzinfo=timezone.utc)
END = START + timedelta(hours=1)


class UndefinedOffset(tzinfo):
    def utcoffset(self, dt):
        return None


@pytest.fixture(params=[RescheduleAppointmentInput, RescheduleAppointmentOutput])
def build_dto(request, make_user):
    def build(**overrides):
        data = {"appointment_id": uuid4(), "start_at": START, "end_at": END}
        if request.param is RescheduleAppointmentInput:
            data["actor"] = make_user()
        else:
            data.update(
                status=AppointmentStatus.SCHEDULED,
                was_deposit_retained=False,
                deposit_override_applied=False,
            )
        data.update(overrides)
        return request.param(**data)

    return build


@pytest.mark.parametrize("field", ["start_at", "end_at"])
@pytest.mark.parametrize(
    "invalid",
    [
        None,
        "2035-01-10T12:00:00Z",
        date(2035, 1, 10),
        START.replace(tzinfo=None),
        START.replace(tzinfo=UndefinedOffset()),
    ],
    ids=["none", "string", "date_only", "naive", "undefined_offset"],
)
def test_rejects_invalid_datetime_in_either_field(build_dto, field, invalid):
    with pytest.raises(AppointmentMustHaveRealisticTimeAndDateError):
        build_dto(**{field: invalid})


@pytest.mark.parametrize(
    "offset", [timedelta(0), timedelta(hours=-3), timedelta(hours=5, minutes=30), timedelta(hours=14)]
)
def test_normalizes_offsets_to_utc_without_changing_instants(build_dto, offset):
    original_start = START.astimezone(timezone(offset))
    original_end = END.astimezone(timezone(offset))
    result = build_dto(start_at=original_start, end_at=original_end)

    assert result.start_at == START
    assert result.end_at == END
    assert result.start_at.tzinfo is timezone.utc
    assert result.end_at.tzinfo is timezone.utc
    assert result.end_at - result.start_at == timedelta(hours=1)
    assert original_start.utcoffset() == offset
    assert original_end.utcoffset() == offset


def test_normalizes_each_endpoint_independently(build_dto):
    result = build_dto(
        start_at=START.astimezone(timezone(timedelta(hours=-3))),
        end_at=END.astimezone(timezone(timedelta(hours=5, minutes=30))),
    )
    assert result.start_at == START
    assert result.end_at == END
    assert result.start_at.tzinfo is result.end_at.tzinfo is timezone.utc


def test_preserves_distinct_instants_during_repeated_daylight_saving_hour(build_dto):
    paris = ZoneInfo("Europe/Paris")
    result = build_dto(
        start_at=datetime(2026, 10, 25, 2, 30, tzinfo=paris, fold=0),
        end_at=datetime(2026, 10, 25, 2, 30, tzinfo=paris, fold=1),
    )
    assert result.start_at == datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc)
    assert result.end_at == datetime(2026, 10, 25, 1, 30, tzinfo=timezone.utc)
    assert result.end_at - result.start_at == timedelta(hours=1)


@pytest.mark.parametrize("field", ["start_at", "end_at"])
def test_dto_remains_frozen_after_normalization(build_dto, field):
    result = build_dto()
    with pytest.raises(FrozenInstanceError):
        setattr(result, field, END + timedelta(hours=1))
