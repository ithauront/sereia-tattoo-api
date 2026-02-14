from uuid import uuid4
from fastapi.testclient import TestClient
from freezegun import freeze_time
from pydantic import SecretStr
from app.api.dependencies.users import get_users_repository
from app.core.security.jwt_service import JWTService
from app.core.security.passwords import hash_password, verify_password
from app.core.security.versioned_token_service import VersionedTokenService
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_reset_password_success(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password="OldPassword1",
        is_active=True,
        is_admin=False,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 204
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is True
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is False
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 1

    app.dependency_overrides.clear()


def test_reset_password_admin_success(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=True,
        is_admin=True,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 204
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is True
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is True
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 1

    app.dependency_overrides.clear()


def test_reset_password_user_not_found(repo):
    not_user_id = uuid4()
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(not_user_id), version=0)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"
    assert user_in_repo is None

    app.dependency_overrides.clear()


def test_reset_password_user_inactive(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=False,
        is_admin=True,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 409
    assert response.json()["detail"] == "user_inactive"
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is False
    assert user_in_repo.is_active is False
    assert user_in_repo.is_admin is True
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 0

    app.dependency_overrides.clear()


def test_reset_password_second_call_route_same_token(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=True,
        is_admin=False,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    first_call = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    second_call = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")
    # A primeira chamada deve dar certo e ela vai dar bump no token
    assert first_call.status_code == 204
    # A segunda chamada vai dar erro porque a versão do token não é mais valida
    assert second_call.status_code == 401
    assert second_call.json()["detail"] == "invalid_activation_token"
    # A primeira chamada atualiza o password e o token version bump 1 vez
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is True
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is False
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 1

    app.dependency_overrides.clear()


def test_reset_password_token_version_greater_than_user(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=True,
        is_admin=False,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=1)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_activation_token"
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is False
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is False
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 0

    app.dependency_overrides.clear()


def test_reset_password_token_version_smaller_than_user(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=True,
        is_admin=False,
        password_token_version=1,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_activation_token"
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is False
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is False
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 1

    app.dependency_overrides.clear()


def test_reset_password_not_valid(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=True,
        is_admin=False,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"new_password": "notvalid"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 422
    assert response.json()["detail"] == "password_needs_uppercase"
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("notvalid", user_in_repo.hashed_password) is False
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is False
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 0

    app.dependency_overrides.clear()


def test_reset_password_wrong_token_type(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=True,
        is_admin=False,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="refresh", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is False
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is False
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 0

    app.dependency_overrides.clear()


def test_reset_password_expired_token(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=True,
        is_admin=False,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with freeze_time("2025-01-01 12:00:00"):
        token_service = VersionedTokenService(
            jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
        )
        token = token_service.create(user_id=str(user.id), version=0)

    with freeze_time("2025-01-01 12:16:00"):
        payload = {"new_password": "NewPassword1"}

        app.dependency_overrides[get_users_repository] = lambda: repo

        response = client.post(
            "/me/reset-password",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is False
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is False
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 0

    app.dependency_overrides.clear()


def test_reset_password_wrong_token_secret_key(repo, make_user):
    user = make_user(
        username="JhonDoe",
        email="jhon@doe.com",
        hashed_password=hash_password("OldPassword1"),
        is_active=True,
        is_admin=False,
        password_token_version=0,
        has_activated_once=True,
    )
    repo.create(user)
    jwt_service = JWTService(
        secret_key=SecretStr("wrong_secret_key"),
        algorithm=settings.JWT_ALGORITHM,
    )
    token_service = VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )
    token = token_service.create(user_id=str(user.id), version=0)

    payload = {"new_password": "NewPassword1"}

    app.dependency_overrides[get_users_repository] = lambda: repo

    response = client.post(
        "/me/reset-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_repo = repo.find_by_email("jhon@doe.com")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user_in_repo.username == "JhonDoe"
    assert verify_password("NewPassword1", user_in_repo.hashed_password) is False
    assert user_in_repo.is_active is True
    assert user_in_repo.is_admin is False
    assert user_in_repo.has_activated_once is True
    assert user_in_repo.password_token_version == 0

    app.dependency_overrides.clear()
