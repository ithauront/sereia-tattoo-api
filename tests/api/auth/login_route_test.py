from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.core.security import jwt_service
from app.main import app


client = TestClient(app)


def test_login_success_with_username(write_uow, read_uow, make_user):
    user = make_user()
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"identifier": user.username, "password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200

    data = response.json()
    access = data["access_token"]
    refresh = data["refresh_token"]

    payload_access = jwt_service.decode(access)
    assert payload_access["sub"] == str(user.id)
    assert payload_access["type"] == "access"

    payload_refresh = jwt_service.decode(refresh)
    assert payload_refresh["sub"] == str(user.id)
    assert payload_refresh["type"] == "refresh"

    app.dependency_overrides = {}


def test_login_success_with_email(write_uow, read_uow, make_user):
    user = make_user()
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"identifier": user.email, "password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200

    data = response.json()
    access = data["access_token"]
    refresh = data["refresh_token"]

    payload_access = jwt_service.decode(access)
    assert payload_access["sub"] == str(user.id)
    assert payload_access["type"] == "access"

    payload_refresh = jwt_service.decode(refresh)
    assert payload_refresh["sub"] == str(user.id)
    assert payload_refresh["type"] == "refresh"

    app.dependency_overrides = {}


def test_wrong_identifier(write_uow, read_uow, make_user):
    user = make_user()
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"identifier": "wrong-user", "password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_not_user(read_uow):

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"identifier": "user", "password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_inactive_user(write_uow, read_uow, make_user):
    user = make_user(is_active=False)
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"identifier": user.email, "password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_wrong_password(write_uow, read_uow, make_user):
    user = make_user()
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"identifier": user.username, "password": "abcde"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_missing_user(write_uow, read_uow, make_user):
    user = make_user()
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "identifier"]

    app.dependency_overrides = {}


def test_missing_password(write_uow, read_uow, make_user):
    user = make_user()
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"identifier": user.username}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "password"]

    app.dependency_overrides = {}


def test_missing_payload(write_uow, read_uow, make_user):
    user = make_user()
    write_uow.users.create(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post("/auth/login")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]

    app.dependency_overrides = {}


def test_login_invalid_payload_types(read_uow):
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"identifier": 123, "password": "123456"}

    response = client.post("/auth/login", json=payload)
    assert response.status_code == 422
