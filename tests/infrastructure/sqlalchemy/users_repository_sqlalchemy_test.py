from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security.passwords import hash_password, verify_password

from app.domain.studio.users.entities.user import User
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)


def test_create_and_find_by_id(
    sqlalchemy_users_repo: SQLAlchemyUsersRepository, make_user
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    found = sqlalchemy_users_repo.find_by_id(user.id)

    assert found is not None
    assert found.email == "jhon@doe.com"
    assert found.id == user.id


def test_unique_constraint_email(
    sqlalchemy_users_repo: SQLAlchemyUsersRepository, make_user
):
    user1 = make_user(email="jhon@doe.com")
    sqlalchemy_users_repo.create(user1)

    user2 = make_user(email="jhon@doe.com")

    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_users_repo.create(user2)

    assert "UNIQUE constraint failed" in str(exc.value)


def test_unique_constraint_username(
    sqlalchemy_users_repo: SQLAlchemyUsersRepository, make_user
):
    user1 = make_user(username="JhonDoe")
    sqlalchemy_users_repo.create(user1)

    user2 = make_user(username="JhonDoe")

    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_users_repo.create(user2)

    assert "UNIQUE constraint failed" in str(exc.value)


def test_nulable_constraint_username(
    sqlalchemy_users_repo: SQLAlchemyUsersRepository, make_user
):
    user = make_user(username=None)

    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_users_repo.create(user)

    assert "NOT NULL constraint failed" in str(exc.value)


def test_nulable_constraint_email(
    sqlalchemy_users_repo: SQLAlchemyUsersRepository, make_user
):
    user = make_user(email=None)

    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_users_repo.create(user)

    assert "NOT NULL constraint failed" in str(exc.value)


def test_defaults_are_applied(
    sqlalchemy_users_repo: SQLAlchemyUsersRepository, make_user
):
    user = make_user(
        is_admin=None,
        is_active=None,
        activation_token_version=None,
    )

    sqlalchemy_users_repo.create(user)
    found = sqlalchemy_users_repo.find_by_id(user.id)

    assert found is not None

    assert found.is_admin is False
    assert found.is_active is False
    assert found.activation_token_version == 0
    assert isinstance(found.is_admin, bool)
    assert isinstance(found.id, UUID)


def test_combined_queries(sqlalchemy_users_repo: SQLAlchemyUsersRepository, make_user):
    user1 = make_user(is_active=True, is_admin=True)
    user2 = make_user(
        username="JackDoe", email="jack@doe.com", is_active=True, is_admin=False
    )
    user3 = make_user(
        username="JaneDoe", email="jane@doe.com", is_active=False, is_admin=False
    )

    sqlalchemy_users_repo.create(user1)
    sqlalchemy_users_repo.create(user2)
    sqlalchemy_users_repo.create(user3)

    found_combined = sqlalchemy_users_repo.find_many(is_admin=True, is_active=True)

    assert len(found_combined) == 1


def test_update_user(sqlalchemy_users_repo: SQLAlchemyUsersRepository, make_user):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    new_user = User(
        id=user.id,
        username=user.username,
        email=user.email,
        hashed_password=hash_password("abcdef"),
        is_admin=True,
        is_active=False,
        created_at=user.created_at,
    )

    before = sqlalchemy_users_repo.find_by_id(user.id)

    sqlalchemy_users_repo.update(new_user)

    after = sqlalchemy_users_repo.find_by_id(user.id)

    assert after is not None
    assert before is not None
    assert after.email == "jhon@doe.com"
    assert before.is_admin is False
    assert after.is_admin is True
    assert before.is_active is True
    assert after.is_active is False
    assert verify_password("abcdef", after.hashed_password)


def test_update_does_not_modify_immutable_fields(sqlalchemy_users_repo, make_user):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    original = sqlalchemy_users_repo.find_by_id(user.id)

    updated_user = User(
        id=user.id,
        username=user.username,
        email=user.email,
        hashed_password=user.hashed_password,
        is_admin=user.is_admin,
        is_active=user.is_active,
        has_activated_once=user.has_activated_once,
        activation_token_version=user.activation_token_version,
        created_at=None,
        updated_at=user.updated_at,
    )

    sqlalchemy_users_repo.update(updated_user)

    result = sqlalchemy_users_repo.find_by_id(user.id)

    assert result is not None
    assert original is not None

    assert result.created_at == original.created_at
