from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.core.security import jwt_service
from app.main import app


client = TestClient(app)


def test_demote_user(repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    repo.create(admin)
    repo.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_demote_nonexistent_user(repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    repo.create(admin)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_route_cannot_demote_yourself(repo, make_user, make_token):
    admin = make_user(is_admin=True, is_active=True)
    repo.create(admin)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "cannot_demote_yourself"


def test_not_admin_demote_user(repo, make_user, make_token):
    not_admin = make_user(is_admin=False)
    user = make_user(is_admin=True)

    repo.create(not_admin)
    repo.create(user)

    token = make_token(not_admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_inactive_admin_demote_user(repo, make_user, make_token):
    inactive_admin = make_user(is_admin=True, is_active=False)
    user = make_user(is_admin=True)

    repo.create(inactive_admin)
    repo.create(user)

    token = make_token(inactive_admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_nonexistent_user_demote_user(repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    repo.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is True

    app.dependency_overrides = {}


def wrong_token_type_demote_user(repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    repo.create(user)

    token = make_token(admin, token_type="refresh")

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_missing_authorization_header(repo, make_user):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    repo.create(admin)
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(f"/users/demote/{user.id}")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_missing_bearer_prefix(repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    repo.create(admin)
    repo.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f" {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_invalid_jwt_format(repo, make_user):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    repo.create(admin)
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_invalid_token_sub(repo, make_user):
    user = make_user(is_admin=True)

    repo.create(user)

    token = jwt_service.create(subject="not-a-uuid", minutes=60, token_type="access")

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f" {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is True

    app.dependency_overrides = {}
