from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.studio.users.entities.user import User


class UsersRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> None: ...

    @abstractmethod
    def update(self, user: User) -> None: ...

    @abstractmethod
    def find_by_id(self, userId: UUID) -> Optional[User]: ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]: ...

    @abstractmethod
    def find_many(
        self, *, is_active: Optional[bool] = None, is_admin: Optional[bool] = None
    ) -> List[User]: ...
