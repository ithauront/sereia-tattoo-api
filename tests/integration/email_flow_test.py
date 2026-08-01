from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.dependencies.events import get_integration_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.application.event_bus.setup import setup_event_bus
from app.main import app
from tests.fakes.fake_email_service import FakeEmailService
from tests.integration.utils.wait_until import wait_until

client = TestClient(app)


# TODO: quando tiver a rota e o script de atualizar o booking window testar se esses fluxos vão enviar o email
def test_create_user_triggers_email(write_uow, read_uow, make_user, make_token, jwt_service_instance):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    with TestClient(app) as client:
        response = client.post(
            "/users",
            json={"email": "jhon@doe.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201

        wait_until(lambda: fake_email_service.sent)

        assert fake_email_service.sent is True
        assert fake_email_service.last_payload is not None
        assert fake_email_service.last_payload["to"] == "jhon@doe.com"

    app.dependency_overrides = {}


def test_create_user_failure_does_not_trigger_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    existing = make_user(email="jhon@doe.com")
    write_uow.users.create(existing)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    with TestClient(app) as client:
        response = client.post(
            "/users",
            json={"email": "jhon@doe.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 409
        assert fake_email_service.sent is False

    app.dependency_overrides = {}


def test_resend_activation_email_triggers_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    with TestClient(app) as client:
        response = client.post(
            "/users/resend-email",
            json={"email": "admin@admin.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        wait_until(lambda: fake_email_service.sent)

        assert fake_email_service.sent is True
        assert fake_email_service.last_payload is not None
        assert fake_email_service.last_payload["to"] == "admin@admin.com"

    app.dependency_overrides = {}


def test_resend_activation_email_error_does_not_triggers_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    with TestClient(app) as client:
        response = client.post(
            "/users/resend-email",
            json={"email": "not_found@admin.com"},
            headers={"Authorization": f"Bearer {token}"},
        )  # email is from a not found user

        assert response.status_code == 404
        assert fake_email_service.sent is False

    app.dependency_overrides = {}


def test_create_vip_client_triggers_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "phone": "71989818232",
        "email": "jhon@doe.com",
        "client_code": "JHON-AZUL",
    }

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    wait_until(lambda: fake_email_service.sent)

    assert fake_email_service.sent is True
    assert fake_email_service.last_payload is not None
    assert fake_email_service.last_payload["to"] == "jhon@doe.com"

    app.dependency_overrides = {}


def test_create_vip_client_failure_does_not_trigger_email(
    write_uow, read_uow, make_user, make_token, make_vip_client, jwt_service_instance
):
    # admin
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    # existing vip client with same client-code to trigger error
    existing = make_vip_client(
        email="other@doe.com",
        phone="11111111111",
        client_code="JHON-AZUL",
    )
    write_uow.vip_clients.create(existing)

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "phone": "71989818232",
        "email": "jhon@doe.com",
        "client_code": "JHON-AZUL",
    }

    response = client.post(
        "vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert fake_email_service.sent is False

    app.dependency_overrides = {}


def test_reset_password_request_triggers_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/me/reset-password-request",
        json={"email": "admin@admin.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    wait_until(lambda: fake_email_service.sent)

    assert fake_email_service.sent is True
    assert fake_email_service.last_payload is not None
    assert fake_email_service.last_payload["to"] == "admin@admin.com"

    app.dependency_overrides = {}


def test_reset_password_request_failure_does_not_trigger_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/me/reset-password-request",
        json={"email": "notfound@doe.com"},
        headers={"Authorization": f"Bearer {token}"},
    )  # email is from a not found user

    assert response.status_code == 200  # route respond 200 even if not found
    assert fake_email_service.sent is False

    app.dependency_overrides = {}


def test_create_appointment_request_triggers_email(
    write_uow,
    read_uow,
    make_user,
    make_calendar_settings,
    jwt_service_instance,
):

    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

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

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 201

    wait_until(lambda: len(fake_email_service.sent_emails) >= 2)

    recipients = {email["to"] for email in fake_email_service.sent_emails}

    assert len(fake_email_service.sent_emails) == 2
    assert recipients == {
        "jane@doe.com",
        "jhon@doe.com",
    }

    app.dependency_overrides = {}


def test_create_appointmnet_request_failure_does_not_trigger_email(
    write_uow, read_uow, make_user, jwt_service_instance, make_calendar_settings
):

    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

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
        # without appointment type should fail
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

    fake_email_service = FakeEmailService()

    _, integration_bus = setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )

    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/appointments",
        json=payload,
    )

    assert response.status_code == 422  # wrong payload should fail request
    assert fake_email_service.sent is False

    app.dependency_overrides = {}
