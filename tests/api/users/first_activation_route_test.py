from uuid import uuid4
from fastapi.testclient import TestClient
from freezegun import freeze_time
from app.core.security.versioned_token_service import VersionedTokenService
from app.core.security.passwords import verify_password
from app.main import app
from app.api.dependencies.users import get_users_repository
from app.core.security.jwt_service import JWTService
from app.core.config import settings


client = TestClient(app)


def test_first_activation_user_success(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 204
    assert user_in_users_repo.username == "JhonDoe"
    assert verify_password("Password1", user_in_users_repo.hashed_password) is True
    assert user_in_users_repo.is_active is True
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is True
    assert user_in_users_repo.activation_token_version == 1

    app.dependency_overrides.clear()


def test_first_activation_admin_success(users_repo, make_user):
    admin = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=True,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(admin)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(admin.id), version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 204
    assert user_in_users_repo.username == "JhonDoe"
    assert verify_password("Password1", user_in_users_repo.hashed_password) is True
    assert user_in_users_repo.is_active is True
    assert user_in_users_repo.is_admin is True
    assert user_in_users_repo.has_activated_once is True
    assert user_in_users_repo.activation_token_version == 1

    app.dependency_overrides.clear()


def test_first_activation_user_not_found(users_repo):
    fake_user_id = uuid4()
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(fake_user_id), version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"
    assert user_in_users_repo is None

    app.dependency_overrides.clear()


def test_first_activation_user_activated_before(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=True,
    )
    users_repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "user_was_activated_before"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is True
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_second_call_route_same_token(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    first_call = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    second_call = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert first_call.status_code == 204

    assert second_call.status_code == 409
    assert second_call.json()["detail"] == "user_was_activated_before"
    assert user_in_users_repo.username == "JhonDoe"
    assert verify_password("Password1", user_in_users_repo.hashed_password) is True
    assert user_in_users_repo.is_active is True
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is True
    assert user_in_users_repo.activation_token_version == 1

    app.dependency_overrides.clear()


def test_first_activation_user_token_version_greater_than_user(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=1)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_activation_token"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_user_token_version_smaller_than_user(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=1,
        has_activated_once=False,
    )
    users_repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_activation_token"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 1

    app.dependency_overrides.clear()


def test_first_activation_username_already_taken(users_repo, make_user):
    first_user = make_user(username="JhonDoe", email="firstjhon@doe.com")
    users_repo.create(first_user)
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "username_already_taken"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_username_against_validation_rules(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"username": "Jh", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 422
    assert response.json()["detail"] == "username_must_have_between_3_and_30_characters"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_user_wrong_token_type(users_repo, make_user, make_token):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)
    token = make_token(user, token_type="refresh")

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_missing_header(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_missing_Bearer_prefix(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)

    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f" {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_invalid_jwt_format(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_invalid_token_sub(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)

    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )
    token = token_service.create(user_id="not_a_uuid", version=0)

    payload = {"username": "JhonDoe", "password": "Password1"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.post(
        "/me/first-activation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()


def test_first_activation_token_expired(users_repo, make_user):
    user = make_user(
        username="",
        email="jhon@doe.com",
        hashed_password="",
        is_active=False,
        is_admin=False,
        activation_token_version=0,
        has_activated_once=False,
    )
    users_repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with freeze_time("2025-01-01 12:00:00"):
        token_service = VersionedTokenService(
            jwt_service=jwt_service, token_type="activation", ttl_minutes=15
        )
        token = token_service.create(user_id=str(user.id), version=0)

    with freeze_time("2025-01-01 12:16:00"):
        payload = {"username": "JhonDoe", "password": "Password1"}
        app.dependency_overrides[get_users_repository] = lambda: users_repo

        response = client.post(
            "/me/first-activation",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    user_in_users_repo = users_repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user_in_users_repo.username == ""
    assert user_in_users_repo.hashed_password == ""
    assert user_in_users_repo.is_active is False
    assert user_in_users_repo.is_admin is False
    assert user_in_users_repo.has_activated_once is False
    assert user_in_users_repo.activation_token_version == 0

    app.dependency_overrides.clear()
