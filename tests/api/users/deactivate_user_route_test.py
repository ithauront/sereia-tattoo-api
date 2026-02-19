from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.core.security import jwt_service
from app.main import app


client = TestClient(app)


def test_deactivate_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_active=True)

    users_repo.create(admin)
    users_repo.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.is_active is False

    app.dependency_overrides = {}


def test_deactivate_nonexistent_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_active=True)

    users_repo.create(admin)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"
    assert user.is_active is True

    app.dependency_overrides = {}


def test_route_cannot_deactivate_yourself(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, is_active=True)
    users_repo.create(admin)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "cannot_deactivate_yourself"


def test_deactivate_user_inactive(users_repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_active=False)

    users_repo.create(admin)
    users_repo.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.is_active is False

    app.dependency_overrides = {}


def test_not_admin_deactivate_user(users_repo, make_user, make_token):
    not_admin = make_user(is_admin=False)
    user = make_user(is_active=True)

    users_repo.create(not_admin)
    users_repo.create(user)

    token = make_token(not_admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert user.is_active is True

    app.dependency_overrides = {}


def test_inactive_admin_deactivate_user(users_repo, make_user, make_token):
    inactive_admin = make_user(is_admin=True, is_active=False)
    user = make_user(is_active=True)

    users_repo.create(inactive_admin)
    users_repo.create(user)

    token = make_token(inactive_admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"
    assert user.is_active is True

    app.dependency_overrides = {}


def test_nonexistent_user_deactivate_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_active=True)

    users_repo.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_active is True

    app.dependency_overrides = {}


def wrong_token_type_deactivate_user(users_repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_active=True)

    users_repo.create(user)

    token = make_token(admin, token_type="refresh")

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_active is True

    app.dependency_overrides = {}


def test_missing_authorization_header(users_repo, make_user):
    admin = make_user(is_admin=True)
    user = make_user(is_active=True)

    users_repo.create(admin)
    users_repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(f"/users/deactivate/{user.id}")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]
    assert user.is_active is True

    app.dependency_overrides = {}


def test_missing_bearer_prefix(users_repo, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_active=True)

    users_repo.create(admin)
    users_repo.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f" {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_active is True

    app.dependency_overrides = {}


def test_invalid_jwt_format(users_repo, make_user):
    admin = make_user(is_admin=True)
    user = make_user(is_active=True)

    users_repo.create(admin)
    users_repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_active is True

    app.dependency_overrides = {}


def test_invalid_token_sub(users_repo, make_user):
    user = make_user(is_active=True)

    users_repo.create(user)

    token = jwt_service.create(subject="not-a-uuid", minutes=60, token_type="access")

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.patch(
        f"/users/deactivate/{user.id}",
        headers={"Authorization": f" {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_active is True

    app.dependency_overrides = {}
