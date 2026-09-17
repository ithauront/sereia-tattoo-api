from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.studio.use_cases.appointments_use_cases.create_appointment_use_case import (
    CreateAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.create_appointment_dto import CreateAppointmentInput
from app.core.exceptions.appointments import (
    AppointmentProjectNotFoundError,
    AppointmentProjectRequiresAuthenticatedUserError,
    SlotIsAlreadyOccupiedError,
    SlotIsNotAvailableError,
    TotalSessionsExceededError,
    TotalSessionsMustMatchProjectError,
)
from app.core.exceptions.calendar import (
    UserIsNotWorkingInDesignatedTimeframeError,
)
from app.core.exceptions.users import UserInactiveError, UserNotFoundError
from app.core.types.appointment_enums import AppointmentStatus, AppointmentType
from app.domain.studio.appointments.entities.appointment import Appointment
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.appointments.policies.appointment_project_policy import (
    AppointmentProjectPolicy,
)
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)
from tests.fakes.fake_event_bus import FakeIntegrationEventBus


def _project_dto(
    *, user_id, client_info, project_id=None, total_sessions=None, actor_id=None
):
    start_at = datetime(2030, 1, 1, 10, tzinfo=timezone.utc)
    return CreateAppointmentInput(
        appointment_type=AppointmentType.TATTOO,
        user_id=user_id,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
        placement="Braço",
        details="Projeto de múltiplas sessões",
        client_info=client_info,
        project_id=project_id,
        total_sessions=total_sessions,
        actor_id=actor_id,
    )


def _create_use_case(write_uow, read_uow):
    return CreateAppointmentUseCase(
        write_uow=write_uow,
        read_uow=read_uow,
        integration_bus=FakeIntegrationEventBus(),
        calendar_policy=CalendarAvailabilityPolicy(),
        project_policy=AppointmentProjectPolicy(),
    )


def _client_info():
    return ClientInfo(
        name="Client",
        email="client@example.com",
        phone="+351910000000",
    )


def test_make_appointment_starts_and_continues_same_project(write_uow, read_uow):
    use_case = _create_use_case(write_uow, read_uow)
    user_id = uuid4()
    client_info = _client_info()

    first, _ = use_case._make_appointment(
        _project_dto(user_id=user_id, client_info=client_info, total_sessions=3)
    )
    write_uow.appointments.create(first)
    second, log = use_case._make_appointment(
        _project_dto(user_id=user_id, client_info=client_info, project_id=first.project_id)
    )

    assert first.project_id is not None
    assert second.project_id == first.project_id
    assert first.current_session == 1
    assert second.current_session == 2
    assert second.total_sessions == 3
    assert log.changes is not None
    initial_state = log.changes["initial_state_must_important_info"]
    assert initial_state["project_id"] == str(first.project_id)
    assert initial_state["current_session"] == 2
    assert initial_state["total_sessions"] == 3


def test_make_appointment_reuses_canceled_session_number(write_uow, read_uow):
    use_case = _create_use_case(write_uow, read_uow)
    user_id = uuid4()
    client_info = _client_info()
    project_id = uuid4()

    first = Appointment.create(
        appointment_type=AppointmentType.TATTOO,
        project_id=project_id,
        user_id=user_id,
        start_at=datetime(2030, 1, 1, 10, tzinfo=timezone.utc),
        end_at=datetime(2030, 1, 1, 11, tzinfo=timezone.utc),
        placement="Braço",
        details="Primeira sessão",
        current_session=1,
        total_sessions=3,
        client_info=client_info,
    )
    canceled_second = Appointment.create(
        appointment_type=AppointmentType.TATTOO,
        project_id=project_id,
        user_id=user_id,
        start_at=datetime(2030, 1, 2, 10, tzinfo=timezone.utc),
        end_at=datetime(2030, 1, 2, 11, tzinfo=timezone.utc),
        placement="Braço",
        details="Segunda sessão cancelada",
        current_session=2,
        total_sessions=3,
        client_info=client_info,
    )
    canceled_second.mark_as_canceled(
        observations="Cliente solicitou reagendamento",
        is_eligible_for_deposit_refund=False,
    )
    write_uow.appointments.create(first)
    write_uow.appointments.create(canceled_second)

    replacement, _ = use_case._make_appointment(
        _project_dto(user_id=user_id, client_info=client_info, project_id=project_id)
    )

    assert replacement.current_session == 2
    assert replacement.total_sessions == 3


def test_make_appointment_fills_canceled_gap_before_later_active_session(
    write_uow, read_uow
):
    use_case = _create_use_case(write_uow, read_uow)
    user_id = uuid4()
    client_info = _client_info()
    project_id = uuid4()

    for current_session, status in (
        (1, AppointmentStatus.REQUESTED),
        (2, AppointmentStatus.CANCELED),
        (3, AppointmentStatus.REQUESTED),
    ):
        appointment = Appointment.create(
            appointment_type=AppointmentType.TATTOO,
            project_id=project_id,
            user_id=user_id,
            start_at=datetime(2030, 1, current_session, 10, tzinfo=timezone.utc),
            end_at=datetime(2030, 1, current_session, 11, tzinfo=timezone.utc),
            placement="Braço",
            details=f"Sessão {current_session}",
            current_session=current_session,
            total_sessions=3,
            client_info=client_info,
        )
        if status == AppointmentStatus.CANCELED:
            appointment.mark_as_canceled(
                observations="Cliente solicitou reagendamento",
                is_eligible_for_deposit_refund=False,
            )
        write_uow.appointments.create(appointment)

    replacement, _ = use_case._make_appointment(
        _project_dto(user_id=user_id, client_info=client_info, project_id=project_id)
    )

    assert replacement.current_session == 2
    assert replacement.total_sessions == 3


def test_make_appointment_rejects_unknown_project(write_uow, read_uow):
    use_case = _create_use_case(write_uow, read_uow)

    with pytest.raises(AppointmentProjectNotFoundError):
        use_case._make_appointment(
            _project_dto(
                user_id=uuid4(),
                client_info=_client_info(),
                project_id=uuid4(),
            )
        )


def test_make_appointment_rejects_different_total(write_uow, read_uow):
    use_case = _create_use_case(write_uow, read_uow)
    user_id = uuid4()
    client_info = _client_info()
    first, _ = use_case._make_appointment(
        _project_dto(user_id=user_id, client_info=client_info, total_sessions=3)
    )
    write_uow.appointments.create(first)

    with pytest.raises(TotalSessionsMustMatchProjectError):
        use_case._make_appointment(
            _project_dto(
                user_id=user_id,
                client_info=client_info,
                project_id=first.project_id,
                total_sessions=4,
            )
        )


def test_make_appointment_rejects_session_after_project_total(write_uow, read_uow):
    use_case = _create_use_case(write_uow, read_uow)
    user_id = uuid4()
    client_info = _client_info()
    project_id = uuid4()
    for current_session in (1, 2):
        appointment = Appointment.create(
            appointment_type=AppointmentType.TATTOO,
            project_id=project_id,
            user_id=user_id,
            start_at=datetime(2030, 1, current_session, 10, tzinfo=timezone.utc),
            end_at=datetime(2030, 1, current_session, 11, tzinfo=timezone.utc),
            placement="Braço",
            details=f"Sessão {current_session}",
            current_session=current_session,
            total_sessions=2,
            client_info=client_info,
        )
        write_uow.appointments.create(appointment)

    with pytest.raises(TotalSessionsExceededError):
        use_case._make_appointment(
            _project_dto(user_id=user_id, client_info=client_info, project_id=project_id)
        )


@pytest.mark.asyncio
async def test_anonymous_client_cannot_manage_project(write_uow, read_uow):
    use_case = _create_use_case(write_uow, read_uow)

    with pytest.raises(AppointmentProjectRequiresAuthenticatedUserError):
        await use_case.execute(
            _project_dto(
                user_id=uuid4(),
                client_info=_client_info(),
                total_sessions=3,
            )
        )


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
        project_policy=AppointmentProjectPolicy(),
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

    result = await use_case.execute(dto)

    appointment_found = read_uow.appointments.find_many(start_date=start_at, end_date=end_at)

    log_found = read_uow.audit_logs.find_many_by_entity_name(entity_name="appointments")

    assert len(appointment_found) == 1
    assert appointment_found[0].user_id == user.id
    assert isinstance(appointment_found[0], Appointment)
    assert result.appointment_id == appointment_found[0].id
    assert result.project_id is None
    assert result.current_session is None
    assert result.total_sessions is None

    assert len(log_found) == 1

    assert len(integration_bus.events) == 1


@pytest.mark.asyncio
async def test_create_appointment_user_not_found(
    make_user,
    write_uow,
    read_uow,
    make_calendar_settings,
    make_vip_client,
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
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    integration_bus = FakeIntegrationEventBus()
    calendar_policy = CalendarAvailabilityPolicy()

    use_case = CreateAppointmentUseCase(
        read_uow=read_uow,
        write_uow=write_uow,
        integration_bus=integration_bus,
        calendar_policy=calendar_policy,
        project_policy=AppointmentProjectPolicy(),
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

    with pytest.raises(UserNotFoundError):
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
        project_policy=AppointmentProjectPolicy(),
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
        project_policy=AppointmentProjectPolicy(),
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
        project_policy=AppointmentProjectPolicy(),
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
        project_policy=AppointmentProjectPolicy(),
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
        project_policy=AppointmentProjectPolicy(),
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
        project_policy=AppointmentProjectPolicy(),
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


@pytest.mark.asyncio
async def test_inactive_user_raises_error(
    make_user, write_uow, read_uow, make_calendar_settings, make_vip_client
):
    user = make_user(is_active=False)
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
        project_policy=AppointmentProjectPolicy(),
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

    with pytest.raises(UserInactiveError):
        await use_case.execute(dto)
