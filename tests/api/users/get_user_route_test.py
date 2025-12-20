from uuid import uuid4
from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.core.security import jwt_service
from app.main import app


client = TestClient(app)


def test_get_different_user_if_admin(repo, make_user, make_token):
    admin = make_user(is_admin=True)
    repo.create(admin)

    user = make_user(is_admin=False, username="Fabio")
    repo.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "Fabio"
    assert isinstance(data, dict)
    assert "username" in data
    assert "id" in data
    assert "email" in data
    assert "is_active" in data
    assert "is_admin" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "hashed_password" not in data
    assert "password" not in data

    app.dependency_overrides = {}


def test_not_admin_get_himself(repo, make_user, make_token):
    user = make_user(is_admin=False, username="Fabio")
    repo.create(user)

    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "Fabio"

    app.dependency_overrides = {}


def test_user_id_not_found(repo, make_user, make_token):
    admin = make_user(is_admin=True)
    repo.create(admin)

    token = make_token(admin)
    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "user_not_found"


def test_user_cannot_get_other_user(repo, make_user, make_token):
    user1 = make_user(is_admin=False, username="Fabio")
    repo.create(user1)

    user2 = make_user(is_admin=False, username="Alice")
    repo.create(user2)

    token = make_token(user1)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user2.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    app.dependency_overrides = {}


def test_inactive_user_cannot_get_himself(repo, make_user, make_token):
    inactive_user = make_user(is_admin=False, username="Fabio", is_active=False)
    repo.create(inactive_user)

    token = make_token(inactive_user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{inactive_user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_inactive_admin_cannot_get_himself(repo, make_user, make_token):
    inactive_admin = make_user(is_admin=True, username="Fabio", is_active=False)
    repo.create(inactive_admin)

    token = make_token(inactive_admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{inactive_admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_inactive_admin_cannot_get_other_user(repo, make_user, make_token):
    inactive_admin = make_user(is_admin=True, username="Fabio", is_active=False)
    repo.create(inactive_admin)

    user = make_user(is_admin=False, username="Alice")
    repo.create(user)

    token = make_token(inactive_admin)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_cannot_get_user(repo, make_user, make_token):
    user = make_user(is_admin=False, username="Fabio")

    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_toke_type(repo, make_user, make_token):
    user = make_user(is_admin=False, username="Fabio")
    repo.create(user)

    token = make_token(user, token_type="refresh")

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_missing_authorization_header(repo, make_user):
    user = make_user(is_admin=False, username="Fabio")
    repo.create(user)
    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user.id}",
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]

    app.dependency_overrides = {}


def test_missing_bearer_prefix(repo, make_user):
    user = make_user(is_admin=False, username="Fabio")
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": "Token: 123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_jwt_format(repo, make_user):

    user = make_user(is_admin=False, username="Fabio")
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_token_sub(repo, make_user):
    user = make_user(is_admin=False, username="Fabio")
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    token = jwt_service.create(subject="not-a-uuid", minutes=60, token_type="access")

    response = client.get(
        f"/users/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}
