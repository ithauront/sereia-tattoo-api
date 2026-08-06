from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.dependencies.events import get_integration_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.main import app

client = TestClient(app)


def test_create_appointment_without_actor_id_route_success(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_calendar_settings,
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

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 201

    found = read_uow.appointments.find_many(user_id=user.id)
    log = read_uow.audit_logs.find_many_by_entity_name(entity_name="appointments")
    assert len(found) == 1
    assert found[0].details == "Dragão chines"
    assert found[0].start_at == start_at
    assert found[0].end_at == end_at
    assert found[0].client_info == ClientInfo(name="Jane Doe", email="jane@doe.com", phone="71988888888")

    assert len(log) == 1
    assert log[0].actor_id is None
    assert log[0].action == "create appointment"


def test_create_appointment_with_actor_id_route_success(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_calendar_settings,
    make_token,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

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

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 201

    found = read_uow.appointments.find_many(user_id=user.id)
    log = read_uow.audit_logs.find_many_by_entity_name(entity_name="appointments")
    assert len(found) == 1
    assert found[0].details == "Dragão chines"
    assert found[0].start_at == start_at
    assert found[0].end_at == end_at

    assert len(log) == 1
    assert log[0].actor_id == admin.id
    assert log[0].action == "create appointment"


def test_create_appointment_with_client_info_vip_client_success(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_calendar_settings,
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

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "vip_client_id": f"{vip_client.id}",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 201

    found = read_uow.appointments.find_many(user_id=user.id)
    log = read_uow.audit_logs.find_many_by_entity_name(entity_name="appointments")
    assert len(found) == 1
    assert found[0].details == "Dragão chines"
    assert found[0].start_at == start_at
    assert found[0].end_at == end_at
    assert found[0].client_info == ClientInfo(vip_client_id=vip_client.id)

    assert len(log) == 1
    assert log[0].actor_id is None
    assert log[0].action == "create appointment"


def test_create_appointment_saves_referral_code_when_provided_route_success(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_calendar_settings,
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

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
        "referral_code": f"{vip_client.client_code.value}",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 201

    found = read_uow.appointments.find_many(user_id=user.id)
    log = read_uow.audit_logs.find_many_by_entity_name(entity_name="appointments")
    assert len(found) == 1
    assert found[0].details == "Dragão chines"
    assert found[0].start_at == start_at
    assert found[0].end_at == end_at
    assert found[0].client_info == ClientInfo(name="Jane Doe", email="jane@doe.com", phone="71988888888")
    assert found[0].referral_code.value == vip_client.client_code.value

    assert len(log) == 1
    assert log[0].actor_id is None
    assert log[0].action == "create appointment"


def test_create_appointment_double_call(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_appointment_base,
    make_calendar_settings,
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

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    first_call = client.post(
        "/appointments",
        json=payload,
    )

    second_call = client.post(
        "/appointments",
        json=payload,
    )

    assert first_call.status_code == 201

    assert second_call.status_code == 400
    assert second_call.json()["detail"] == "the_time_slot_required_is_occupied"


def test_create_appointment_in_ocuppied_slot(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_appointment_base,
    make_calendar_settings,
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

    existing_appointment = make_appointment_base(user_id=user.id, start_at=start_at, end_at=end_at)
    write_uow.appointments.create(existing_appointment)

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )
    write_uow.calendar_settings.create(calendar_settings)

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "the_time_slot_required_is_occupied"


def test_create_appointment_outside_booking_window(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_appointment_base,
    make_calendar_settings,
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
    month_before = base_now - timedelta(days=35)
    booking_window_until = (base_now + timedelta(days=30)).date()

    start_at = month_before + timedelta(hours=1)
    end_at = month_before + timedelta(hours=2)

    existing_appointment = make_appointment_base(user_id=user.id, start_at=start_at, end_at=end_at)
    write_uow.appointments.create(existing_appointment)

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )
    write_uow.calendar_settings.create(calendar_settings)

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "the_time_slot_required_is_not_available"


def test_create_appointment_admin_can_bypass_booking_window(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_appointment_base,
    make_calendar_settings,
    make_token,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

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
    month_before = base_now - timedelta(days=35)
    booking_window_until = (base_now + timedelta(days=30)).date()

    start_at = month_before + timedelta(hours=1)
    end_at = month_before + timedelta(hours=2)

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )
    write_uow.calendar_settings.create(calendar_settings)

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 201


def test_create_appointment_user_owned_can_bypass_booking_window(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_appointment_base,
    make_calendar_settings,
    make_token,
):

    user = make_user()
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    month_before = base_now - timedelta(days=35)
    booking_window_until = (base_now + timedelta(days=30)).date()

    start_at = month_before + timedelta(hours=1)
    end_at = month_before + timedelta(hours=2)

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )
    write_uow.calendar_settings.create(calendar_settings)

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )

    assert response.status_code == 201


def test_create_appointment_in_exception_timeframe(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_calendar_exception,
    make_calendar_settings,
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
    month_before = base_now - timedelta(days=35)
    booking_window_until = (base_now + timedelta(days=30)).date()

    start_at = month_before + timedelta(hours=1)
    end_at = month_before + timedelta(hours=2)

    calendar_exception = make_calendar_exception(user_id=user.id, start_at=start_at, end_at=end_at)
    write_uow.calendar_exceptions.create(calendar_exception)

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )
    write_uow.calendar_settings.create(calendar_settings)

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "the_time_slot_required_is_not_available"


def test_create_appointment_in_outside_working_period(
    make_user,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_working_period,
    make_calendar_settings,
):
    user = make_user()
    write_uow.users.create(user)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    days_until_next_sunday = (6 - base_now.weekday()) % 7 or 7
    next_sunday = base_now + timedelta(days=days_until_next_sunday)
    booking_window_until = (base_now + timedelta(days=30)).date()

    start_at = next_sunday.replace(hour=9)
    end_at = next_sunday.replace(hour=10)
    monday_to_saturday = [make_working_period(weekday=weekday) for weekday in range(6)]

    calendar_settings = make_calendar_settings(
        user_id=user.id,
        booking_window_until=booking_window_until,
        working_periods=monday_to_saturday,
    )
    write_uow.calendar_settings.create(calendar_settings)

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "the_time_slot_required_is_not_available"


def test_create_appointment_in_without_calendar_of_user(
    make_user,
    write_uow,
    read_uow,
    fake_integration_event_bus,
):
    user = make_user()
    write_uow.users.create(user)

    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    days_until_next_sunday = (6 - base_now.weekday()) % 7 or 7
    next_sunday = base_now + timedelta(days=days_until_next_sunday)

    start_at = next_sunday.replace(hour=9)
    end_at = next_sunday.replace(hour=10)

    # we do not create calendar for this test

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "the_time_slot_required_is_not_available"


def test_create_appointment_without_vip_client_id_or_contact_info(
    make_user,
    write_uow,
    read_uow,
    fake_integration_event_bus,
):
    user = make_user()
    write_uow.users.create(user)

    start_at = datetime.now(timezone.utc) + timedelta(days=1)
    end_at = start_at + timedelta(hours=1)

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Non_VIP_clients_must_provide_name_email_and_phone"


def test_create_appointment_wrong_payload(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_calendar_settings,
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

    payload = {
        "appointment_type": "tattoo",
        # without user_id
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 422


def test_create_user_not_exist_raise_400(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_calendar_settings,
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

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "user_does_not_exists_or_is_inactive"


def test_create_user_inactive_raise_400(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_calendar_settings,
):
    user = make_user()

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

    payload = {
        "appointment_type": "tattoo",
        "user_id": f"{user.id}",
        "start_at": f"{start_at}",
        "end_at": f"{end_at}",
        "placement": "ombro",
        "details": "Dragão chines",
        "size": "30cm",
        "color": True,
        "name": "Jane Doe",
        "email": "jane@doe.com",
        "phone": "71988888888",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "user_does_not_exists_or_is_inactive"
