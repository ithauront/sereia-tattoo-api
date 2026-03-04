from freezegun import freeze_time
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_refresh_success(write_uow, read_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    write_uow.users.create(user)
    refresh_token = make_token(user=user, version=0, token_type="refresh")

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post("/auth/refresh/", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    user_in_users_repo = read_uow.users.find_by_id(user.id)
    assert user_in_users_repo.access_token_version == 0
    assert user_in_users_repo.refresh_token_version == 0

    data = response.json()
    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["refresh_token"] != refresh_token

    app.dependency_overrides = {}


def test_refresh_with_revoked_token(write_uow, read_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=1)
    write_uow.users.create(user)
    refresh_token = make_token(user=user, version=0, token_type="refresh")

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post("/auth/refresh/", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    user_in_users_repo = read_uow.users.find_by_id(user.id)
    assert user_in_users_repo.access_token_version == 0
    assert user_in_users_repo.refresh_token_version == 1

    data = response.json()
    assert data["detail"] == "token_revoked"
    assert "access_token" not in data
    assert "refresh_token" not in data

    app.dependency_overrides = {}


def test_refresh_non_user(write_uow, read_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    refresh_token = make_token(user=user, version=0, token_type="refresh")

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post("/auth/refresh/", json={"refresh_token": refresh_token})

    assert response.status_code == 401

    data = response.json()
    assert data["detail"] == "invalid_credentials"
    assert "access_token" not in data
    assert "refresh_token" not in data

    app.dependency_overrides = {}


def test_refresh_twice(write_uow, read_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    write_uow.users.create(user)
    refresh_token = make_token(user=user, version=0, token_type="refresh")

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    first_try = client.post("/auth/refresh/", json={"refresh_token": refresh_token})
    second_try = client.post("/auth/refresh/", json={"refresh_token": refresh_token})

    assert first_try.status_code == 200
    user_in_users_repo = read_uow.users.find_by_id(user.id)
    assert user_in_users_repo.access_token_version == 0
    assert user_in_users_repo.refresh_token_version == 0

    data_first_try = first_try.json()
    assert data_first_try["access_token"] is not None
    assert data_first_try["refresh_token"] is not None
    assert data_first_try["refresh_token"] != refresh_token

    assert second_try.status_code == 200
    user_in_users_repo = read_uow.users.find_by_id(user.id)
    assert user_in_users_repo.access_token_version == 0
    assert user_in_users_repo.refresh_token_version == 0

    data_second_try = second_try.json()
    assert data_second_try["access_token"] is not None
    assert data_second_try["refresh_token"] is not None
    assert data_second_try["refresh_token"] != refresh_token

    assert data_first_try["refresh_token"] != data_second_try["refresh_token"]
    app.dependency_overrides = {}


def test_refresh_inactive_user(read_uow, write_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0, is_active=False)
    write_uow.users.create(user)
    token = make_token(user=user, version=0, token_type="refresh")

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post("/auth/refresh/", json={"refresh_token": token})

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "invalid_credentials"
    assert "access_token" not in data
    assert "refresh_token" not in data

    app.dependency_overrides = {}


def test_refresh_token_expired(write_uow, read_uow, make_user, make_token):
    user = make_user(access_token_version=0, refresh_token_version=0)
    write_uow.users.create(user)
    with freeze_time("2025-01-01 12:16:00"):
        refresh_token = make_token(user=user, version=0, token_type="refresh")

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow
    with freeze_time("2025-01-04 12:16:10"):  # refresh token expira em 4 dias
        response = client.post("/auth/refresh/", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    user_in_users_repo = read_uow.users.find_by_id(user.id)
    assert user_in_users_repo.access_token_version == 0
    assert user_in_users_repo.refresh_token_version == 0

    data = response.json()
    assert data["detail"] == "invalid_token"
    assert "access_token" not in data
    assert "refresh_token" not in data

    app.dependency_overrides = {}
