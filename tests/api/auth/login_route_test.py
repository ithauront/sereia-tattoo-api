from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.core.security import jwt_service
from app.main import app


client = TestClient(app)


def test_login_success_with_username(repo, make_user):
    user = make_user()
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

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


def test_login_success_with_email(repo, make_user):
    user = make_user()
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

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


def test_wrong_identifier(repo, make_user):
    user = make_user()
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"identifier": "wrong-user", "password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_not_user(repo):

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"identifier": "user", "password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_inactive_user(repo, make_user):
    user = make_user(is_active=False)
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"identifier": user.email, "password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_wrong_password(repo, make_user):
    user = make_user()
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"identifier": user.username, "password": "abcde"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_missing_user(repo, make_user):
    user = make_user()
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "123456"}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "identifier"]

    app.dependency_overrides = {}


def test_missing_password(repo, make_user):
    user = make_user()
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"identifier": user.username}

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "password"]

    app.dependency_overrides = {}


def test_missing_payload(repo, make_user):
    user = make_user()
    repo.create(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post("/auth/login")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]

    app.dependency_overrides = {}


def test_login_invalid_payload_types(repo):
    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"identifier": 123, "password": "123456"}

    response = client.post("/auth/login", json=payload)
    assert response.status_code == 422


# TODO: fazer testes de falha
