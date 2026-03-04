from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_logout_success(write_uow, read_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    write_uow.users.create(user)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    user_in_users_repo = read_uow.users.find_by_id(user.id)
    assert user_in_users_repo.access_token_version == 1
    assert user_in_users_repo.refresh_token_version == 1

    app.dependency_overrides = {}


def test_logout_user_not_found(read_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.access_token_version == 0
    assert user.refresh_token_version == 0

    app.dependency_overrides = {}


def test_logout_with_revoked_token(write_uow, read_uow, make_user, make_token):
    user = make_user(access_token_version=1, refresh_token_version=1)
    write_uow.users.create(user)

    token = make_token(user=user, version=0)  # versão antiga

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401

    app.dependency_overrides = {}


def test_logout_twice(write_uow, read_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    write_uow.users.create(user)
    token = make_token(user=user, version=0)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

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


def test_logout_and_and_try_other_route(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True, access_token_version=0, refresh_token_version=0)
    write_uow.users.create(admin)
    token = make_token(user=admin, version=0)
    user = make_user(is_admin=True, access_token_version=0, refresh_token_version=0)
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    logout = client.post(
        "/auth/logout/",
        headers={"Authorization": f"Bearer {token}"},
    )

    demote = client.patch(
        f"/users/demote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )  # just another route that needs auth token

    assert logout.status_code == 204
    assert demote.status_code == 401

    app.dependency_overrides = {}
