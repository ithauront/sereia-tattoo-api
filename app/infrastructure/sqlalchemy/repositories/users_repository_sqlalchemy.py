from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from app.domain.users.repositories.users_repository import UsersRepository
from sqlalchemy.orm import Session

from app.domain.users.entities.user import User

from app.infrastructure.sqlalchemy.models.users import UserModel


class SQLAlchemyUsersRepository(UsersRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, user: User) -> None:
        orm_user = UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            is_admin=user.is_admin,
            is_active=user.is_active,
            has_activated_once=user.has_activated_once,
            activation_token_version=user.activation_token_version,
        )
        self.session.add(orm_user)
        self.session.flush()

    def update(self, user: User) -> None:
        user_in_question = select(UserModel).where(UserModel.id == user.id)

        orm_user = self.session.scalar(user_in_question)
        if orm_user is None:
            return

        orm_user.username = user.username
        orm_user.email = user.email
        orm_user.hashed_password = user.hashed_password
        orm_user.is_active = user.is_active
        orm_user.is_admin = user.is_admin
        orm_user.has_activated_once = user.has_activated_once
        orm_user.activation_token_version = user.activation_token_version

        self.session.flush()

    def find_by_id(self, userId: UUID) -> Optional[User]:
        user_in_question = select(UserModel).where(UserModel.id == userId)
        orm_user = self.session.scalar(user_in_question)

        return self._to_entity(orm_user)

    def find_by_email(self, email: str) -> Optional[User]:
        user_in_question = select(UserModel).where(UserModel.email == email)
        orm_user = self.session.scalar(user_in_question)

        return self._to_entity(orm_user)

    def find_by_username(self, username: str) -> Optional[User]:
        user_in_question = select(UserModel).where(UserModel.username == username)
        orm_user = self.session.scalar(user_in_question)

        return self._to_entity(orm_user)

    def find_many(
        self, *, is_active: Optional[bool] = None, is_admin: Optional[bool] = None
    ) -> List[User]:
        users_in_question = select(UserModel)

        if is_active is not None:
            users_in_question = users_in_question.where(
                UserModel.is_active == is_active
            )

        if is_admin is not None:
            users_in_question = users_in_question.where(UserModel.is_admin == is_admin)

        orm_users = self.session.scalars(users_in_question).all()
        entities = []
        for orm_user in orm_users:
            entity = self._to_entity(orm_user)
            if entity is not None:
                entities.append(entity)
        return entities

    def _to_entity(self, orm_user: Optional[UserModel]) -> Optional[User]:
        if orm_user is None:
            return None

        return User(
            id=UUID(str(orm_user.id)),
            username=orm_user.username,
            email=orm_user.email,
            hashed_password=orm_user.hashed_password,
            is_admin=orm_user.is_admin,
            is_active=orm_user.is_active,
            has_activated_once=orm_user.has_activated_once,
            activation_token_version=orm_user.activation_token_version,
            created_at=orm_user.created_at,
            updated_at=orm_user.updated_at,
        )
