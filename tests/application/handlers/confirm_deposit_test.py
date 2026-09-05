from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.studio.handlers.confirm_deposit import ConfirmDepositHandler
from app.core.exceptions.appointments import (
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentNotFoundError,
)
from app.core.types.appointment_enums import AppointmentStatus
from app.domain.studio.finances.events.deposit_payment_recorded_event import (
    DepositPaymentRecordedEvent,
)


async def test_confirm_deposit_updates_quoted_appointment(
    write_uow,
    make_quoted_appointment,
):
    appointment = make_quoted_appointment()
    write_uow.appointments.create(appointment)
    event = DepositPaymentRecordedEvent(
        appointment_id=appointment.id,
        amount=Decimal("50"),
    )

    await ConfirmDepositHandler().handle(event, uow=write_uow)

    updated_appointment = write_uow.appointments.find_by_id(appointment.id)
    assert updated_appointment is not None
    assert updated_appointment.status == AppointmentStatus.SCHEDULED
    assert updated_appointment.deposit_confirmed_at is not None


async def test_confirm_deposit_rejects_unknown_appointment(write_uow):
    event = DepositPaymentRecordedEvent(
        appointment_id=uuid4(),
        amount=Decimal("50"),
    )

    with pytest.raises(AppointmentNotFoundError):
        await ConfirmDepositHandler().handle(event, uow=write_uow)


async def test_confirm_deposit_rejects_appointment_in_wrong_status(
    write_uow,
    make_scheduled_appointment,
):
    appointment = make_scheduled_appointment()
    write_uow.appointments.create(appointment)
    event = DepositPaymentRecordedEvent(
        appointment_id=appointment.id,
        amount=Decimal("50"),
    )

    with pytest.raises(AppointmentMustBeInCorrectPreviousStatusError):
        await ConfirmDepositHandler().handle(event, uow=write_uow)
