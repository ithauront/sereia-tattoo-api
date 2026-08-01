from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.studio.use_cases.appointments_use_cases.create_appointment_use_case import (
    CreateAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.create_appointment_dto import CreateAppointmentInput
from app.core.exceptions.appointments import SlotIsAlreadyOccupiedError, SlotIsNotAvailableError
from app.core.exceptions.calendar import (
    CannotFindWorkingPeriodsForThisUserError,
    UserIsNotWorkingInDesignatedTimeframeError,
)
from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)
from tests.fakes.fake_event_bus import FakeIntegrationEventBus


@pytest.mark.asyncio
async def test_create_appointment_successful(
    make_user, write_uow, read_uow, make_calendar_settings, make_vip_client
):
    user = make_user()
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )
    write_uow.calendar_settings.create(calendar_settings)

    integration_bus = FakeIntegrationEventBus()
    calendar_policy = CalendarAvailabilityPolicy()

    use_case = CreateAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=integration_bus,
        calendar_policy=calendar_policy,
    )

    client_info = ClientInfo(vip_client_id=vip_client.id)
    dto = CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        placement="Ombro",
        details="Tatuagem de dragão oriental",
        size="25cm",
        color=True,
        client_info=client_info,
        referral_code=vip_client.client_code,
        actor_id=None,
    )

    await use_case.execute(dto)

    appointment_found = read_uow.appointments.find_many(start_date=start_at, end_date=end_at)

    log_found = read_uow.audit_logs.find_many_by_entity_name(entity_name="appointments")

    assert len(appointment_found) == 1
    assert appointment_found[0].user_id == user.id
    assert isinstance(appointment_found[0], Appointment)

    assert len(log_found) == 1

    assert len(integration_bus.events) == 1


@pytest.mark.asyncio
async def test_create_appointment_calendar_of_user_not_found(
    make_user, write_uow, read_uow, make_calendar_settings, make_vip_client
):
    user = make_user()
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )
    write_uow.calendar_settings.create(calendar_settings)

    integration_bus = FakeIntegrationEventBus()
    calendar_policy = CalendarAvailabilityPolicy()

    use_case = CreateAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=integration_bus,
        calendar_policy=calendar_policy,
    )

    client_info = ClientInfo(vip_client_id=vip_client.id)
    dto = CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=uuid4(),
        start_at=start_at,
        end_at=end_at,
        placement="Ombro",
        details="Tatuagem de dragão oriental",
        size="25cm",
        color=True,
        client_info=client_info,
        referral_code=vip_client.client_code,
        actor_id=user.id,
    )

    with pytest.raises(CannotFindWorkingPeriodsForThisUserError):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_cannot_create_in_occupy_slot(
    make_user, write_uow, read_uow, make_calendar_settings, make_vip_client
):
    user = make_user()
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )
    write_uow.calendar_settings.create(calendar_settings)

    integration_bus = FakeIntegrationEventBus()
    calendar_policy = CalendarAvailabilityPolicy()

    use_case = CreateAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=integration_bus,
        calendar_policy=calendar_policy,
    )

    client_info = ClientInfo(vip_client_id=vip_client.id)
    dto = CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        placement="Ombro",
        details="Tatuagem de dragão oriental",
        size="25cm",
        color=True,
        client_info=client_info,
        referral_code=vip_client.client_code,
        actor_id=user.id,
    )

    await use_case.execute(dto)  # This will occupy the slot

    with pytest.raises(SlotIsAlreadyOccupiedError):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_create_appointment_outside_booking_window_without_permission(
    make_user, write_uow, make_calendar_settings, make_vip_client, read_uow
):
    user = make_user()
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )

    booking_window_until = (base_now + timedelta(days=30)).date()

    start_at = base_now + timedelta(days=60, hours=1)
    end_at = base_now + timedelta(days=60, hours=2)

    calendar_settings = make_calendar_settings(
        user_id=user.id,
        booking_window_until=booking_window_until,
    )

    write_uow.calendar_settings.create(calendar_settings)

    use_case = CreateAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=FakeIntegrationEventBus(),
        calendar_policy=CalendarAvailabilityPolicy(),
    )

    dto = CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        placement="Ombro",
        details="Teste booking window",
        size="20cm",
        color=True,
        client_info=ClientInfo(vip_client_id=vip_client.id),
        referral_code=vip_client.client_code,
        actor_id=None,
    )

    with pytest.raises(SlotIsNotAvailableError):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_admin_can_create_outside_booking_window(
    make_user, write_uow, read_uow, make_calendar_settings, make_vip_client
):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )

    calendar_settings = make_calendar_settings(
        user_id=admin.id,
        booking_window_until=(base_now + timedelta(days=30)).date(),
    )

    write_uow.calendar_settings.create(calendar_settings)

    start_at = base_now + timedelta(days=60, hours=1)
    end_at = start_at + timedelta(hours=1)

    integration_bus = FakeIntegrationEventBus()

    use_case = CreateAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=integration_bus,
        calendar_policy=CalendarAvailabilityPolicy(),
    )

    dto = CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=admin.id,
        start_at=start_at,
        end_at=end_at,
        placement="Braço",
        details="Admin appointment",
        size="15cm",
        color=False,
        client_info=ClientInfo(vip_client_id=vip_client.id),
        referral_code=vip_client.client_code,
        actor_id=admin.id,
    )

    await use_case.execute(dto)

    appointments = read_uow.appointments.find_many(
        start_date=start_at,
        end_date=end_at,
    )

    assert len(appointments) == 1


@pytest.mark.asyncio
async def test_calendar_owner_can_create_outside_booking_window(
    make_user, write_uow, read_uow, make_calendar_settings, make_vip_client
):
    user = make_user()
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )

    calendar_settings = make_calendar_settings(
        user_id=user.id,
        booking_window_until=(base_now + timedelta(days=30)).date(),
    )

    write_uow.calendar_settings.create(calendar_settings)

    start_at = base_now + timedelta(days=60, hours=1)
    end_at = start_at + timedelta(hours=1)

    use_case = CreateAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=FakeIntegrationEventBus(),
        calendar_policy=CalendarAvailabilityPolicy(),
    )

    dto = CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        placement="Perna",
        details="Owner appointment",
        size="30cm",
        color=True,
        client_info=ClientInfo(vip_client_id=vip_client.id),
        referral_code=vip_client.client_code,
        actor_id=user.id,
    )

    await use_case.execute(dto)

    appointments = read_uow.appointments.find_many(
        start_date=start_at,
        end_date=end_at,
    )

    assert len(appointments) == 1


@pytest.mark.asyncio
async def test_user_cannot_ignore_other_users_booking_window(
    make_user, write_uow, read_uow, make_calendar_settings, make_vip_client
):
    owner = make_user()
    actor = make_user()

    write_uow.users.create(owner)
    write_uow.users.create(actor)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )

    calendar_settings = make_calendar_settings(
        user_id=owner.id,
        booking_window_until=(base_now + timedelta(days=30)).date(),
    )

    write_uow.calendar_settings.create(calendar_settings)

    start_at = base_now + timedelta(days=60, hours=1)
    end_at = start_at + timedelta(hours=1)

    use_case = CreateAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=FakeIntegrationEventBus(),
        calendar_policy=CalendarAvailabilityPolicy(),
    )

    dto = CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=owner.id,
        start_at=start_at,
        end_at=end_at,
        placement="Costas",
        details="Other user calendar",
        size="20cm",
        color=False,
        client_info=ClientInfo(vip_client_id=vip_client.id),
        referral_code=vip_client.client_code,
        actor_id=actor.id,
    )

    with pytest.raises(SlotIsNotAvailableError):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_create_appointment_blocked_by_calendar_exception(
    make_user,
    write_uow,
    read_uow,
    make_calendar_settings,
    make_vip_client,
    make_calendar_exception,
):
    user = make_user()
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )

    start_at = base_now + timedelta(days=1, hours=1)
    end_at = start_at + timedelta(hours=1)

    calendar_settings = make_calendar_settings(
        user_id=user.id,
        booking_window_until=(base_now + timedelta(days=30)).date(),
    )

    write_uow.calendar_settings.create(calendar_settings)

    exception = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at,
        end_at=end_at,
    )

    write_uow.calendar_exceptions.create(exception)

    use_case = CreateAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=FakeIntegrationEventBus(),
        calendar_policy=CalendarAvailabilityPolicy(),
    )

    dto = CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        placement="Braço",
        details="Blocked appointment",
        client_info=ClientInfo(vip_client_id=vip_client.id),
        referral_code=vip_client.client_code,
        actor_id=user.id,
    )

    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        await use_case.execute(dto)
