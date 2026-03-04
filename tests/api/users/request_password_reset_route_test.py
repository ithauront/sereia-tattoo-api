from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.main import app
from tests.fakes.fake_email_service import FakeEmailService
from app.api.dependencies.notifications import get_email_service


client = TestClient(app)


def test_request_reset_password_success(write_uow, read_uow, make_user):
    user = make_user(email="jhon@doe.com", password_token_version=0)
    write_uow.users.create(user)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/me/reset-password-request",
        json=payload,
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "if user exists and is active a link was sent to reset password"
    )

    assert fake_email_service.sent is True
    assert fake_email_service.last_payload["to"] == "jhon@doe.com"
    assert fake_email_service.last_payload["subject"] == "Recuperação de senha"
    assert (
        "Para criar uma nova senha, clique no botão abaixo:"
        in fake_email_service.last_payload["html"]
    )
    assert user.password_token_version == 1

    app.dependency_overrides.clear()


def test_request_reset_password_user_inactive(write_uow, read_uow, make_user):
    user = make_user(email="jhon@doe.com", is_active=False, password_token_version=0)
    write_uow.users.create(user)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/me/reset-password-request",
        json=payload,
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "if user exists and is active a link was sent to reset password"
    )  # Aqui uso uma mensagem generica para não dar info sobre situação de possivel usuario

    assert fake_email_service.sent is False
    assert user.password_token_version == 0

    app.dependency_overrides.clear()


def test_request_reset_password_user_not_found(read_uow, write_uow):
    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post("/me/reset-password-request", json=payload)

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "if user exists and is active a link was sent to reset password"
    )  # Aqui uso uma mensagem generica para não dar info sobre situação de possivel usuario

    assert fake_email_service.sent is False

    app.dependency_overrides.clear()


def test_request_reset_password_invalid_payload():
    response = client.post("/me/reset-password-request", json={})

    assert response.status_code == 422
