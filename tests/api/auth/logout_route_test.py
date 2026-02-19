from app.api.dependencies.users import get_users_repository
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_logout_success(users_repo, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    users_repo.create(user)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    user_in_users_repo = users_repo.find_by_id(user.id)
    assert user_in_users_repo.access_token_version == 1
    assert user_in_users_repo.refresh_token_version == 1

    app.dependency_overrides = {}


def test_logout_user_not_found(users_repo, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.access_token_version == 0
    assert user.refresh_token_version == 0

    app.dependency_overrides = {}


# TODO: Talvez fazer um teste em que fazemos o logout de um admin e depois tentamos fazer uma nova req com o token que ele tinha para ver se realmente deslogou
def test_logout_with_revoked_token(users_repo, make_user, make_token):
    user = make_user(access_token_version=1, refresh_token_version=1)
    users_repo.create(user)

    token = make_token(user=user, version=0)  # versão antiga

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401

    app.dependency_overrides = {}


def test_logout_twice(users_repo, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    users_repo.create(user)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

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
