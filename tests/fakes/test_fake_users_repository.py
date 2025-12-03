from uuid import uuid4
import pytest

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
            hashed_password="123456",
            is_active=kwargs.get("is_active", True),
            is_admin=kwargs.get("is_admin", False),
        )

    return _factory


def test_create_and_find_by_id(repo, make_user):
    user = make_user()
    repo.create(user)

    found = repo.find_by_id(user.id)
    assert found is not None
    assert found.id == user.id


def test_find_by_email(repo, make_user):
    user = make_user()
    repo.create(user)

    found = repo.find_by_email(user.email)
    not_found = repo.find_by_email("wrong@email.com")

    assert found is not None
    assert found.email == "jhon@doe.com"
    assert not_found is None


def test_find_by_username(repo, make_user):
    user = make_user()
    repo.create(user)
    found = repo.find_by_username("JhonDoe")
    not_found = repo.find_by_username("wrongUserName")

    assert found is not None
    assert found.username == "JhonDoe"
    assert not_found is None


def test_update(repo, make_user):
    user = make_user()
    repo.create(user)
    user = User(
        id=user.id,
        username="NewName",
        email="jhon@doe.com",
        hashed_password="123456",
        is_active=True,
        is_admin=True,
    )
    repo.update(user)

    found = repo.find_by_username("NewName")
    not_found = repo.find_by_username("JhonDoe")

    assert found is not None
    assert found.username == "NewName"
    assert not_found is None


def test_find_many(repo, make_user):
    user1 = make_user(is_active=True, is_admin=True)
    user2 = make_user(is_active=True, is_admin=False)
    user3 = make_user(is_active=False, is_admin=False)

    repo.create(user1)
    repo.create(user2)
    repo.create(user3)

    found_actives = repo.find_many(is_active=True)
    found_inactives = repo.find_many(is_active=False)
    found_not_admins = repo.find_many(is_admin=False)
    found_all = repo.find_many()
    found_combined = repo.find_many(is_admin=True, is_active=True)

    assert len(found_actives) == 2
    assert len(found_inactives) == 1
    assert len(found_not_admins) == 2
    assert len(found_all) == 3
    assert len(found_combined) == 1
