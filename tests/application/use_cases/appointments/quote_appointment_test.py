from decimal import Decimal

import pytest

from app.application.studio.use_cases.appointments_use_cases.quote_appointment_use_case import (
    QuoteAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.quote_appointement_dto import QuoteAppointmentInput
from app.core.exceptions.appointments import (
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentNotFoundError,
    OnlyAdminOrOwnerOfAppointmentError,
    PriceMustBePositiveError,
)
from app.core.types.appointment_enums import AppointmentStatus
from app.core.types.audit_actor_type import AuditActorType
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from tests.fakes.fake_event_bus import FakeIntegrationEventBus


@pytest.mark.asyncio
async def test_quote_appointment_successful(make_user, make_appointment_base, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)

    appointment = make_appointment_base(user_id=user.id)
    write_uow.appointments.create(appointment)

    integration_bus = FakeIntegrationEventBus()
    appointment_authorization_policy = AppointmentAuthorizationPolicy()

    use_case = QuoteAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=integration_bus,
        appointment_authorization_policy=appointment_authorization_policy,
    )
    dto = QuoteAppointmentInput(actor=user, appointment_id=appointment.id, price=Decimal("700"))

    await use_case.execute(dto)

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)

    assert appointment_in_repo.status == AppointmentStatus.QUOTED
    assert appointment_in_repo.price == Decimal("700")

    assert len(integration_bus.events) == 1
    event = integration_bus.events[0]

    assert event.appointment_type == appointment.appointment_type

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert len(logs) == 1
    log = logs[0]

    assert log.entity_name == "appointments"
    assert log.entity_id == appointment.id
    assert log.action == "quote appointment"
    assert log.actor_id == user.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {"price_quoted": "700"}


@pytest.mark.asyncio
async def test_quote_appointment_inexistent(make_user, make_appointment_base, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)

    appointment = make_appointment_base(user_id=user.id)
    # we do not persist appointment for this test

    integration_bus = FakeIntegrationEventBus()
    appointment_authorization_policy = AppointmentAuthorizationPolicy()

    use_case = QuoteAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=integration_bus,
        appointment_authorization_policy=appointment_authorization_policy,
    )
    dto = QuoteAppointmentInput(actor=user, appointment_id=appointment.id, price=Decimal("700"))

    with pytest.raises(AppointmentNotFoundError):
        await use_case.execute(dto)

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert len(logs) == 0
    assert len(integration_bus.events) == 0


@pytest.mark.asyncio
async def test_quote_auth_policy_can_block(make_user, make_appointment_base, write_uow, read_uow):
    not_owner = make_user()
    write_uow.users.create(not_owner)

    owner = make_user()
    write_uow.users.create(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    integration_bus = FakeIntegrationEventBus()
    appointment_authorization_policy = AppointmentAuthorizationPolicy()

    use_case = QuoteAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=integration_bus,
        appointment_authorization_policy=appointment_authorization_policy,
    )
    dto = QuoteAppointmentInput(actor=not_owner, appointment_id=appointment.id, price=Decimal("700"))

    with pytest.raises(OnlyAdminOrOwnerOfAppointmentError):
        await use_case.execute(dto)

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)
    appointment_in_repo = read_uow.appointments.find_by_id(appointment.id)

    assert appointment_in_repo.status != AppointmentStatus.QUOTED
    assert len(logs) == 0
    assert len(integration_bus.events) == 0


@pytest.mark.asyncio
async def test_cannot_quote_if_status_is_not_requested(
    make_user, make_scheduled_appointment, write_uow, read_uow
):
    user = make_user()
    write_uow.users.create(user)

    appointment = make_scheduled_appointment(user_id=user.id)
    write_uow.appointments.create(appointment)

    integration_bus = FakeIntegrationEventBus()
    appointment_authorization_policy = AppointmentAuthorizationPolicy()

    use_case = QuoteAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=integration_bus,
        appointment_authorization_policy=appointment_authorization_policy,
    )
    dto = QuoteAppointmentInput(actor=user, appointment_id=appointment.id, price=Decimal("700"))

    with pytest.raises(AppointmentMustBeInCorrectPreviousStatusError):
        await use_case.execute(dto)

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)
    appointment_in_repo = read_uow.appointments.find_by_id(appointment.id)

    assert appointment_in_repo.status != AppointmentStatus.QUOTED
    assert len(logs) == 0
    assert len(integration_bus.events) == 0


@pytest.mark.asyncio
async def test_cannot_quote_if_price_is_negative(make_user, make_appointment_base, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)

    appointment = make_appointment_base(user_id=user.id)
    write_uow.appointments.create(appointment)

    integration_bus = FakeIntegrationEventBus()
    appointment_authorization_policy = AppointmentAuthorizationPolicy()

    use_case = QuoteAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=integration_bus,
        appointment_authorization_policy=appointment_authorization_policy,
    )
    dto = QuoteAppointmentInput(actor=user, appointment_id=appointment.id, price=Decimal("-10"))

    with pytest.raises(PriceMustBePositiveError):
        await use_case.execute(dto)

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)
    appointment_in_repo = read_uow.appointments.find_by_id(appointment.id)

    assert appointment_in_repo.status != AppointmentStatus.QUOTED
    assert len(logs) == 0
    assert len(integration_bus.events) == 0


@pytest.mark.asyncio
async def test_cannot_quote_if_price_is_zero(make_user, make_appointment_base, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)

    appointment = make_appointment_base(user_id=user.id)
    write_uow.appointments.create(appointment)

    integration_bus = FakeIntegrationEventBus()
    appointment_authorization_policy = AppointmentAuthorizationPolicy()

    use_case = QuoteAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=integration_bus,
        appointment_authorization_policy=appointment_authorization_policy,
    )
    dto = QuoteAppointmentInput(actor=user, appointment_id=appointment.id, price=Decimal("0"))

    with pytest.raises(PriceMustBePositiveError):
        await use_case.execute(dto)

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)
    appointment_in_repo = read_uow.appointments.find_by_id(appointment.id)

    assert appointment_in_repo.status != AppointmentStatus.QUOTED
    assert len(logs) == 0
    assert len(integration_bus.events) == 0
