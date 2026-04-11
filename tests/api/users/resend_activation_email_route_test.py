from fastapi.testclient import TestClient
from app.api.dependencies.events import get_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.main import app


client = TestClient(app)


def test_resend_activation_email_success(
    write_uow, read_uow, make_user, fake_event_bus
):
    user = make_user(
        email="jhon@doe.com",
    )
    write_uow.users.create(user)

    payload = {"email": "jhon@doe.com"}

    app.dependency_overrides[get_event_bus] = lambda: fake_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/resend-email",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Activation email request accepted"
    assert user.activation_token_version == 1

    app.dependency_overrides.clear()


def test_resend_user_already_activated_once(
    write_uow, read_uow, make_user, fake_event_bus
):
    user = make_user(
        email="jhon@doe.com", has_activated_once=True, activation_token_version=1
    )
    write_uow.users.create(user)

    payload = {"email": "jhon@doe.com"}

    app.dependency_overrides[get_event_bus] = lambda: fake_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/resend-email",
        json=payload,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "user_has_been_activated_before"

    assert user.activation_token_version == 1

    app.dependency_overrides.clear()


def test_resend_email_user_not_found(write_uow, read_uow, fake_event_bus):
    payload = {"email": "jhon@doe.com"}

    app.dependency_overrides[get_event_bus] = lambda: fake_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post("/users/resend-email", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"

    app.dependency_overrides.clear()


def test_resend_email_invalid_payload(fake_event_bus):
    app.dependency_overrides[get_event_bus] = lambda: fake_event_bus

    response = client.post("/users/resend-email", json={})

    assert response.status_code == 422
