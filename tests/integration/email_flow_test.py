from fastapi.testclient import TestClient

from app.api.dependencies.events import get_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.application.event_bus.setup import setup_event_bus
from tests.fakes.fake_email_service import FakeEmailService

from app.main import app


client = TestClient(app)


def test_create_user_triggers_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    with TestClient(app) as client:
        response = client.post(
            "/users",
            json={"email": "jhon@doe.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        assert fake_email_service.sent is True
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

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
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

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    with TestClient(app) as client:
        response = client.post(
            "/users/resend-email",
            json={"email": "admin@admin.com"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert fake_email_service.sent is True
        assert fake_email_service.last_payload["to"] == "admin@admin.com"

    app.dependency_overrides = {}


def test_resend_activation_email_error_does_not_triggers_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
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

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert fake_email_service.sent is True
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

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
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

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/me/reset-password-request",
        json={"email": "admin@admin.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert fake_email_service.sent is True
    assert fake_email_service.last_payload["to"] == "admin@admin.com"

    app.dependency_overrides = {}


def test_reset_password_request_failure_does_not_trigger_email(
    write_uow, read_uow, make_user, make_token, jwt_service_instance
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=fake_email_service,
        token_service=jwt_service_instance,
    )
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
