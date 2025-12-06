from uuid import uuid4
import pytest

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
            hashed_password=hash_password("123456"),
            is_active=kwargs.get("is_active", True),
            is_admin=kwargs.get("is_admin", False),
        )

    return _factory
