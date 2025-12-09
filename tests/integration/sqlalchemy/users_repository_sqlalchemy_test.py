from freezegun import freeze_time

from app.core.security.passwords import hash_password, verify_password
from app.domain.users.entities.user import User
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)


def test_create_and_find_by_id(sqlalchemy_repo: SQLAlchemyUsersRepository, make_user):
    user = make_user()
    sqlalchemy_repo.create(user)

    found = sqlalchemy_repo.find_by_id(user.id)

    assert found is not None
    assert found.email == "jhon@doe.com"
    assert found.id == user.id


def test_find_by_email(sqlalchemy_repo: SQLAlchemyUsersRepository, make_user):
    user = make_user()
    sqlalchemy_repo.create(user)

    found = sqlalchemy_repo.find_by_email(user.email)

    assert found is not None
    assert found.email == "jhon@doe.com"
    assert found.id == user.id


def test_find_by_username(sqlalchemy_repo: SQLAlchemyUsersRepository, make_user):

    user = make_user()
    sqlalchemy_repo.create(user)

    found = sqlalchemy_repo.find_by_username(user.username)

    assert found is not None
    assert found.username == "JhonDoe"
    assert found.id == user.id


def test_find_many(sqlalchemy_repo: SQLAlchemyUsersRepository, make_user):
    user1 = make_user(is_active=True, is_admin=True)
    user2 = make_user(
        username="JackDoe", email="jack@doe.com", is_active=True, is_admin=False
    )
    user3 = make_user(
        username="JaneDoe", email="jane@doe.com", is_active=False, is_admin=False
    )

    sqlalchemy_repo.create(user1)
    sqlalchemy_repo.create(user2)
    sqlalchemy_repo.create(user3)

    found_actives = sqlalchemy_repo.find_many(is_active=True)
    found_inactives = sqlalchemy_repo.find_many(is_active=False)
    found_not_admins = sqlalchemy_repo.find_many(is_admin=False)
    found_all = sqlalchemy_repo.find_many()
    found_combined = sqlalchemy_repo.find_many(is_admin=True, is_active=True)

    assert len(found_actives) == 2
    assert len(found_inactives) == 1
    assert len(found_not_admins) == 2
    assert len(found_all) == 3
    assert len(found_combined) == 1


def test_update_user(sqlalchemy_repo: SQLAlchemyUsersRepository, make_user):
    user = make_user()
    with freeze_time("2025-01-01 12:00:00"):
        sqlalchemy_repo.create(user)
    new_user = User(
        id=user.id,
        username=user.username,
        email=user.email,
        hashed_password=hash_password("abcdef"),
        is_admin=True,
        is_active=False,
        created_at=user.created_at,
    )

    with freeze_time("2025-01-01 12:00:10"):
        sqlalchemy_repo.update(new_user)

    updated_user = sqlalchemy_repo.find_by_id(user.id)

    assert updated_user is not None
    assert updated_user.email == "jhon@doe.com"
    assert updated_user.is_admin is True
    assert updated_user.is_active is False
    assert verify_password("abcdef", updated_user.hashed_password)
    assert updated_user.updated_at > updated_user.created_at
