from app.api.dependencies.users import get_users_repository
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_logout_success(repo, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    repo.create(user)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    user_in_repo = repo.find_by_id(user.id)
    assert user_in_repo.access_token_version == 1
    assert user_in_repo.refresh_token_version == 1

    app.dependency_overrides = {}


def test_logout_user_not_found(repo, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.access_token_version == 0
    assert user.refresh_token_version == 0

    app.dependency_overrides = {}


def test_logout_with_revoked_token(repo, make_user, make_token):
    user = make_user(access_token_version=1, refresh_token_version=1)
    repo.create(user)

    token = make_token(user=user, version=0)  # versão antiga

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401

    app.dependency_overrides = {}


def test_logout_twice(repo, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    repo.create(user)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_users_repository] = lambda: repo

    first_try = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    second_try = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first_try.status_code == 204
    assert second_try.status_code == 401

    app.dependency_overrides = {}
