from datetime import datetime, timedelta, timezone

import pytest

from app.application.studio.use_cases.appointments_use_cases.cancel_appointment_use_case import (
    CancelAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.cancel_appointment import CancelAppointmentInput
from app.core.exceptions.appointments import (
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentNotFoundError,
    OnlyAdminOrOwnerOfAppointmentError,
)
from app.core.exceptions.validation import ValidationError
from app.core.types.appointment_enums import AppointmentStatus
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from app.domain.studio.appointments.policies.deposit_policy import DepositPolicy
from tests.fakes.fake_event_bus import FakeIntegrationEventBus


def _use_case(write_uow, read_uow, integration_bus):
    return CancelAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=integration_bus,
        appointment_authorization_policy=AppointmentAuthorizationPolicy(),
        deposit_policy=DepositPolicy(),
    )


@pytest.mark.asyncio
async def test_cancel_scheduled_appointment_marks_deposit_as_refundable(
    make_user,
    make_scheduled_appointment,
    write_uow,
    read_uow,
):
    actor = make_user()
    now = datetime.now(timezone.utc)
    appointment = make_scheduled_appointment(
        user_id=actor.id,
        start_at=now + timedelta(hours=49),
        end_at=now + timedelta(hours=50),
    )
    write_uow.appointments.create(appointment)
    integration_bus = FakeIntegrationEventBus()

    await _use_case(write_uow, read_uow, integration_bus).execute(
        CancelAppointmentInput(
            appointment_id=appointment.id,
            actor=actor,
            reason="Cliente não poderá comparecer",
        )
    )

    assert appointment.status == AppointmentStatus.CANCELED
    assert appointment.observations is not None
    assert "Cliente não poderá comparecer" in appointment.observations
    assert len(integration_bus.events) == 1
    event = integration_bus.events[0]
    assert event.has_confirmed_deposit is True
    assert event.is_eligible_for_deposit_refund is True

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)
    assert len(logs) == 1
    assert logs[0].actor_id == actor.id
    assert logs[0].reason == "Cliente não poderá comparecer"
    assert logs[0].changes == {
        "status": {"from": "scheduled", "to": "canceled"},
        "is_eligible_for_deposit_refund": True,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("has_deposit", "hours_until_appointment"),
    [(False, 49), (True, 47)],
)
async def test_cancellation_is_not_refundable_without_deposit_or_inside_48_hours(
    has_deposit,
    hours_until_appointment,
    make_user,
    make_appointment_base,
    make_scheduled_appointment,
    write_uow,
    read_uow,
):
    actor = make_user()
    now = datetime.now(timezone.utc)
    make_appointment = make_scheduled_appointment if has_deposit else make_appointment_base
    appointment = make_appointment(
        user_id=actor.id,
        start_at=now + timedelta(hours=hours_until_appointment),
        end_at=now + timedelta(hours=hours_until_appointment + 1),
    )
    write_uow.appointments.create(appointment)
    integration_bus = FakeIntegrationEventBus()

    await _use_case(write_uow, read_uow, integration_bus).execute(
        CancelAppointmentInput(
            appointment_id=appointment.id,
            actor=actor,
            reason="Cancelamento sem reembolso",
        )
    )

    event = integration_bus.events[0]
    assert event.has_confirmed_deposit is has_deposit
    assert event.is_eligible_for_deposit_refund is False


@pytest.mark.asyncio
async def test_cancel_appointment_requires_reason(make_user, make_appointment_base, write_uow, read_uow):
    actor = make_user()
    appointment = make_appointment_base(user_id=actor.id)
    write_uow.appointments.create(appointment)
    integration_bus = FakeIntegrationEventBus()

    with pytest.raises(ValidationError, match="text_required"):
        await _use_case(write_uow, read_uow, integration_bus).execute(
            CancelAppointmentInput(
                appointment_id=appointment.id,
                actor=actor,
                reason="   ",
            )
        )

    assert appointment.status == AppointmentStatus.REQUESTED
    assert integration_bus.events == []


@pytest.mark.asyncio
async def test_cancel_appointment_rejects_unknown_appointment(make_user, write_uow, read_uow):
    actor = make_user()
    integration_bus = FakeIntegrationEventBus()

    with pytest.raises(AppointmentNotFoundError):
        await _use_case(write_uow, read_uow, integration_bus).execute(
            CancelAppointmentInput(
                appointment_id=actor.id,
                actor=actor,
                reason="Não existe",
            )
        )

    assert integration_bus.events == []


@pytest.mark.asyncio
async def test_cancel_appointment_requires_owner_or_admin(
    make_user, make_appointment_base, write_uow, read_uow
):
    owner = make_user()
    another_user = make_user()
    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)
    integration_bus = FakeIntegrationEventBus()

    with pytest.raises(OnlyAdminOrOwnerOfAppointmentError):
        await _use_case(write_uow, read_uow, integration_bus).execute(
            CancelAppointmentInput(
                appointment_id=appointment.id,
                actor=another_user,
                reason="Sem permissão",
            )
        )

    assert appointment.status == AppointmentStatus.REQUESTED
    assert integration_bus.events == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "terminal_status",
    [AppointmentStatus.CANCELED, AppointmentStatus.COMPLETED],
)
async def test_cancel_appointment_rejects_terminal_status(
    terminal_status,
    make_user,
    make_appointment_base,
    make_completed_appointment,
    write_uow,
    read_uow,
):
    actor = make_user()
    if terminal_status == AppointmentStatus.COMPLETED:
        appointment = make_completed_appointment(user_id=actor.id)
    else:
        appointment = make_appointment_base(
            user_id=actor.id,
            status=AppointmentStatus.CANCELED,
        )
    write_uow.appointments.create(appointment)
    integration_bus = FakeIntegrationEventBus()

    with pytest.raises(AppointmentMustBeInCorrectPreviousStatusError):
        await _use_case(write_uow, read_uow, integration_bus).execute(
            CancelAppointmentInput(
                appointment_id=appointment.id,
                actor=actor,
                reason="Estado terminal",
            )
        )

    assert integration_bus.events == []
    assert read_uow.audit_logs.find_many_by_entity_id(appointment.id) == []
