from fastapi.testclient import TestClient
from app.core.security import jwt_service
from app.main import app
from app.api.dependencies.users import get_users_repository
from tests.fakes.fake_email_service import FakeEmailService
from app.api.dependencies.notifications import get_email_service


client = TestClient(app)


def test_create_user_success(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    users_repo.create(admin)

    token = make_token(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is not None

    assert response.status_code == 200
    assert response.json()["message"] == "User created and activation mail sent"

    assert fake_email_service.sent is True
    assert fake_email_service.last_payload["to"] == "jhon@doe.com"
    assert fake_email_service.last_payload["subject"] == "Ative sua conta"
    assert (
        "Você foi convidado para criar uma conta"
        in fake_email_service.last_payload["html"]
    )

    app.dependency_overrides = {}


def test_user_already_exists(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    user = make_user(email="jhon@doe.com")
    users_repo.create(admin)
    users_repo.create(user)

    token = make_token(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert fake_email_service.sent is False
    assert response.status_code == 409
    assert response.json()["detail"] == "user_already_exists"

    app.dependency_overrides = {}


def test_email_service_unavalible(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    users_repo.create(admin)

    token = make_token(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService(fail_with="email_service_unavailable")

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_email_service] = lambda: fake_email_service

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "email_service_unavailable"

    app.dependency_overrides = {}


def test_email_send_failed(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    users_repo.create(admin)

    token = make_token(admin)

    payload = {"email": "jhon@doe.com"}
    fake_email_service = FakeEmailService(fail_with="email_send_failed")

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "email_send_failed"

    app.dependency_overrides = {}


def test_not_admin_create_user(users_repo, make_user, make_token):
    not_admin = make_user(is_admin=False, email="admin@admin.com")
    users_repo.create(not_admin)

    token = make_token(not_admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    app.dependency_overrides = {}


def test_inactive_admin_create_user(users_repo, make_user, make_token):
    inactive_admin = make_user(is_admin=True, email="admin@admin.com", is_active=False)
    users_repo.create(inactive_admin)

    token = make_token(inactive_admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_non_existent_user_create_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")

    token = make_token(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_token_type_create_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    users_repo.create(admin)

    token = make_token(admin, token_type="refresh")

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_missing_authorization_header_create_user(users_repo, make_user):
    admin = make_user(is_admin=True, email="admin@admin.com")
    users_repo.create(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]

    app.dependency_overrides = {}


def test_missing_bearer_prefix_create_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    users_repo.create(admin)

    token = make_token(admin, token_type="refresh")

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f" {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_jwt_format_create_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    users_repo.create(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_token_sub_create_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    users_repo.create(admin)

    token = jwt_service.create(subject="not-a-uuid", minutes=60, token_type="access")

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/users", json=payload, headers={"Authorization": f" {token}"}
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}
