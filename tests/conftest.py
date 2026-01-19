from uuid import uuid4
import pytest

from app.core.security import jwt_service
from app.core.security.passwords import hash_password
from app.domain.users.entities.user import User
from tests.fakes.fake_users_repository import FakeUsersRepository


@pytest.fixture
def repo():
    return FakeUsersRepository()


@pytest.fixture
def make_user():
    def _factory(**kwargs):
        return User(
            id=uuid4(),
            username=kwargs.get("username", "JhonDoe"),
            email=kwargs.get("email", "jhon@doe.com"),
            hashed_password=kwargs.get(
                "hashed_password", hash_password("123456")
            ),
            is_active=kwargs.get("is_active", True),
            is_admin=kwargs.get("is_admin", False),
            activation_token_version=kwargs.get("activation_token_version", 0),
            has_activated_once=kwargs.get("has_activated_once", False),
        )

    return _factory


@pytest.fixture
def make_token():
    def _factory(user, minutes=60, token_type="access"):
        return jwt_service.create(
            subject=str(user.id), minutes=minutes, token_type=token_type
        )

    return _factory
