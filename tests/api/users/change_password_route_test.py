from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.main import app
from app.core.security.passwords import verify_password

client = TestClient(app)


def test_change_password_success(users_repo, make_user, make_token):
    user = make_user()
    users_repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    payload = {"old_password": "123456", "new_password": "StrongPassword1"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    assert verify_password("StrongPassword1", user.hashed_password)

    app.dependency_overrides = {}


def test_change_password_invalid_old_password(users_repo, make_user, make_token):
    user = make_user()
    users_repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    payload = {"old_password": "wrong_password", "new_password": "StrongPassword1"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert verify_password("123456", user.hashed_password)

    app.dependency_overrides = {}


def test_inactive_user_change_password(users_repo, make_user, make_token):
    user = make_user(is_active=False)
    users_repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_change_password(users_repo, make_user, make_token):
    user = make_user()
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_token_type(users_repo, make_user, make_token):
    user = make_user()
    users_repo.create(user)
    token = make_token(user, token_type="refresh")

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_payload_types(users_repo, make_user, make_token):
    user = make_user()
    users_repo.create(user)

    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    payload = {"old_password": 123, "new_password": "abcdef"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
