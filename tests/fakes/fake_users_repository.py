from typing import List, Optional
from uuid import UUID
from app.domain.users.entities.user import User
from app.domain.users.repositories.users_repository import UsersRepository


class FakeUsersRepository(UsersRepository):
    def __init__(self):
        self.users: List[User] = []

    def create(self, user: User) -> None:
        self.users.append(user)

    def update(self, user: User) -> None:
        for index, user_in_bank in enumerate(self.users):
            if user_in_bank.id == user.id:
                self.users[index] = user
                return

    def find_by_id(self, userId: UUID) -> Optional[User]:
        for user_in_bank in self.users:
            if user_in_bank.id == userId:
                return user_in_bank
        return None

    def find_by_email(self, email: str) -> Optional[User]:
        for user_in_bank in self.users:
            if user_in_bank.email == email:
                return user_in_bank
        return None

    def find_by_username(self, username: str) -> Optional[User]:
        for user_in_bank in self.users:
            if user_in_bank.username == username:
                return user_in_bank
        return None

    def find_many(
        self, *, is_active: Optional[bool] = None, is_admin: Optional[bool] = None
    ) -> List[User]:
        result: List[User] = []
        for user in self.users:
            if is_active is not None and user.is_active != is_active:
                continue
            if is_admin is not None and user.is_admin != is_admin:
                continue
            result.append(user)
        return result
