from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies.users import get_users_repository
from tests.fakes.fake_email_service import FakeEmailService
from app.api.dependencies.notifications import get_email_service


client = TestClient(app)


def test_resend_activation_email_success(repo, make_user):
    user = make_user(
        email="jhon@doe.com",
    )
    repo.create(user)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/users/resend-email",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Activation mail sent"

    assert fake_email_service.sent is True
    assert fake_email_service.last_payload["to"] == "jhon@doe.com"
    assert fake_email_service.last_payload["subject"] == "Ative sua conta"
    assert (
        "Você foi convidado para criar uma conta"
        in fake_email_service.last_payload["html"]
    )
    assert user.activation_token_version == 1

    app.dependency_overrides.clear()


def test_resend_user_already_activated_once(repo, make_user):
    user = make_user(
        email="jhon@doe.com", has_activated_once=True, activation_token_version=1
    )
    repo.create(user)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/users/resend-email",
        json=payload,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "user_has_been_activated_before"

    assert fake_email_service.sent is False
    assert user.activation_token_version == 1

    app.dependency_overrides.clear()


def test_resend_email_user_not_found(repo):
    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post("/users/resend-email", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"
    assert fake_email_service.sent is False

    app.dependency_overrides.clear()


def test_email_service_unavailable(repo, make_user):
    user = make_user(
        email="jhon@doe.com",
    )
    repo.create(user)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService(fail_with="email_service_unavailable")

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post("/users/resend-email", json=payload)

    assert response.status_code == 502
    assert response.json()["detail"] == "email_service_unavailable"
    assert user.activation_token_version == 0
    assert fake_email_service.sent is False

    app.dependency_overrides.clear()


def test_email_send_failed(repo, make_user):
    user = make_user(
        email="jhon@doe.com",
    )
    repo.create(user)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService(fail_with="email_send_failed")

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post("/users/resend-email", json=payload)

    assert response.status_code == 500
    assert response.json()["detail"] == "email_send_failed"
    assert user.activation_token_version == 0
    assert fake_email_service.sent is False

    app.dependency_overrides.clear()


def test_resend_email_invalid_payload():
    response = client.post("/users/resend-email", json={})

    assert response.status_code == 422
