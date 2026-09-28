from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.types.payment_enums import PaymentPurposeType
from app.domain.studio.appointments.policies.deposit_policy import DepositPolicy

START_AT = datetime(2035, 1, 10, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("advance", "expected"),
    [
        (timedelta(hours=48, microseconds=-1), False),
        (timedelta(hours=48), True),
        (timedelta(hours=48, microseconds=1), True),
        (timedelta(0), False),
        (timedelta(hours=-1), False),
    ],
)
def test_transfer_requires_48_hours_before_original_start(
    advance,
    expected,
    make_scheduled_appointment,
    make_payment,
):
    appointment = make_scheduled_appointment(start_at=START_AT, end_at=START_AT + timedelta(hours=2))
    payment = make_payment(appointment_id=appointment.id, payment_purpose=PaymentPurposeType.DEPOSIT)
    assert (
        DepositPolicy().is_deposit_transferable_on_reschedule(
            appointment=appointment,
            payments=[payment],
            reschedule_at=START_AT - advance,
        )
        is expected
    )


@pytest.mark.parametrize("scenario", ["empty", "other_purpose", "retained", "other_appointment"])
def test_transfer_requires_active_deposit_for_this_appointment(
    scenario,
    make_scheduled_appointment,
    make_payment,
):
    appointment = make_scheduled_appointment(start_at=START_AT, end_at=START_AT + timedelta(hours=2))
    payment = make_payment(
        appointment_id=uuid4() if scenario == "other_appointment" else appointment.id,
        payment_purpose=(
            PaymentPurposeType.APPOINTMENT if scenario == "other_purpose" else PaymentPurposeType.DEPOSIT
        ),
    )
    if scenario == "retained":
        payment.retain_deposit(reason="Previous reschedule", retained_at=START_AT - timedelta(days=4))
    assert (
        DepositPolicy().is_deposit_transferable_on_reschedule(
            appointment=appointment,
            payments=[] if scenario == "empty" else [payment],
            reschedule_at=START_AT - timedelta(days=3),
        )
        is False
    )


def test_unconfirmed_deposit_is_not_transferable(make_quoted_appointment, make_payment):
    appointment = make_quoted_appointment(start_at=START_AT, end_at=START_AT + timedelta(hours=2))
    payment = make_payment(appointment_id=appointment.id, payment_purpose=PaymentPurposeType.DEPOSIT)
    assert (
        DepositPolicy().is_deposit_transferable_on_reschedule(
            appointment=appointment,
            payments=[payment],
            reschedule_at=START_AT - timedelta(days=3),
        )
        is False
    )


def test_active_deposit_remains_transferable_with_retained_deposit_in_history(
    make_scheduled_appointment,
    make_payment,
):
    appointment = make_scheduled_appointment(start_at=START_AT, end_at=START_AT + timedelta(hours=2))
    retained = make_payment(appointment_id=appointment.id, payment_purpose=PaymentPurposeType.DEPOSIT)
    retained.retain_deposit(reason="Previous reschedule", retained_at=START_AT - timedelta(days=4))
    active = make_payment(appointment_id=appointment.id, payment_purpose=PaymentPurposeType.DEPOSIT)
    assert (
        DepositPolicy().is_deposit_transferable_on_reschedule(
            appointment=appointment,
            payments=[retained, active],
            reschedule_at=START_AT - timedelta(hours=48),
        )
        is True
    )


def test_transfer_compares_instants_across_timezones(make_scheduled_appointment, make_payment):
    appointment = make_scheduled_appointment(start_at=START_AT, end_at=START_AT + timedelta(hours=2))
    payment = make_payment(appointment_id=appointment.id, payment_purpose=PaymentPurposeType.DEPOSIT)
    reschedule_at = (START_AT - timedelta(hours=48)).astimezone(timezone(timedelta(hours=-3)))
    assert (
        DepositPolicy().is_deposit_transferable_on_reschedule(
            appointment=appointment,
            payments=[payment],
            reschedule_at=reschedule_at,
        )
        is True
    )


def test_transfer_uses_elapsed_hours_across_daylight_saving(make_scheduled_appointment, make_payment):
    from zoneinfo import ZoneInfo

    paris = ZoneInfo("Europe/Paris")
    requested = datetime(2030, 3, 30, 9, tzinfo=paris)
    start = datetime(2030, 4, 1, 9, tzinfo=paris)
    # Two wall-clock days, but only 47 elapsed hours across the spring transition.
    appointment = make_scheduled_appointment(start_at=start, end_at=start + timedelta(hours=1))
    payment = make_payment(appointment_id=appointment.id, payment_purpose=PaymentPurposeType.DEPOSIT)
    assert (
        DepositPolicy().is_deposit_transferable_on_reschedule(
            appointment=appointment,
            payments=[payment],
            reschedule_at=requested,
        )
        is False
    )
