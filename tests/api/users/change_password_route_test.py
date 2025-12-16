from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.core.security import jwt_service
from app.main import app
from app.core.security.passwords import verify_password

client = TestClient(app)


def test_change_password_success(repo, make_user, make_token):
    user = make_user()
    repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.post(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    assert verify_password("abcdef", user.hashed_password)

    app.dependency_overrides = {}


def test_inactive_user_change_password(repo, make_user, make_token):
    user = make_user(is_active=False)
    repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo
    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.post(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_change_password(repo, make_user, make_token):
    user = make_user()
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.post(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_token_type(repo, make_user, make_token):
    user = make_user()
    repo.create(user)
    token = make_token(user, token_type="refresh")

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.post(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_missing_authorization_header(repo):
    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.post(
        "/me/change-password",
        json=payload,
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]

    app.dependency_overrides = {}


def test_missing_bearer_prefix(repo):
    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.post(
        "/me/change-password", json=payload, headers={"Authorization": "Token 123"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_jwt_format(repo):
    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.post(
        "/me/change-password",
        json=payload,
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_token_sub(repo):
    app.dependency_overrides[get_users_repository] = lambda: repo

    token = jwt_service.create(subject="not-a-uuid", minutes=60, token_type="access")

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.post(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_payload_types(repo, make_user, make_token):
    user = make_user()
    repo.create(user)

    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"old_password": 123, "new_password": "abcdef"}

    response = client.post(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
