from uuid import uuid4
import pytest
from app.core.security import jwt_service
from app.core.security.jwt_service import JWTService
from app.core.security.passwords import hash_password
from app.core.security.versioned_token_service import VersionedTokenService
from app.domain.users.entities.user import User
from app.domain.users.entities.value_objects.client_code import ClientCode
from app.domain.users.entities.vip_client import VipClient
from tests.fakes.fake_users_repository import FakeUsersRepository
from app.core.config import settings
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository


@pytest.fixture
def users_repo():
    return FakeUsersRepository()


@pytest.fixture
def vip_clients_repo():
    return FakeVipClientsRepository()


@pytest.fixture
def make_user():
    def _factory(**kwargs):
        return User(
            id=uuid4(),
            username=kwargs.get("username", "JhonDoe"),
            email=kwargs.get("email", "jhon@doe.com"),
            hashed_password=kwargs.get("hashed_password", hash_password("123456")),
            is_active=kwargs.get("is_active", True),
            is_admin=kwargs.get("is_admin", False),
            activation_token_version=kwargs.get("activation_token_version", 0),
            has_activated_once=kwargs.get("has_activated_once", False),
            password_token_version=kwargs.get("password_token_version", 0),
            access_token_version=kwargs.get("access_token_version", 0),
            refresh_token_version=kwargs.get("refresh_token_version", 0),
        )

    return _factory


@pytest.fixture
def make_token():
    def _factory(user, version=None, minutes=60, token_type="access"):
        if version is None:
            if token_type == "access":
                version = user.access_token_version
            else:
                version = user.refresh_token_version
        return jwt_service.create(
            subject=str(user.id),
            minutes=minutes,
            token_type=token_type,
            extra_claims={"ver": version},
        )

    return _factory


@pytest.fixture
def jwt_service_instance():
    return JWTService(secret_key=settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def access_token_service(jwt_service_instance):
    return VersionedTokenService(
        jwt_service_instance, token_type="access", ttl_minutes=60
    )


@pytest.fixture
def refresh_token_service(jwt_service_instance):
    return VersionedTokenService(
        jwt_service_instance, token_type="refresh", ttl_minutes=60
    )


@pytest.fixture
def make_vip_client():
    def _factory(**kwargs):
        return VipClient(
            id=uuid4(),
            first_name=kwargs.get("first_name", "Jhon"),
            last_name=kwargs.get("last_name", "Doe"),
            email=kwargs.get("email", "jhon@doe.com"),
            phone=kwargs.get("phone", "71999999999"),
            client_code=ClientCode(kwargs.get("client_code", "JHON-BLUE")),
        )

    return _factory
