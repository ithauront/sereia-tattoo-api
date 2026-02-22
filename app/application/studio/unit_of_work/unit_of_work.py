from abc import ABC, abstractmethod

from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.repositories.vip_clients_repository import (
    VipClientsRepository,
)


class UnitOfWork(ABC):
    users: UsersRepository
    vip_clients: VipClientsRepository

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        return self

    @abstractmethod
    def __exit__(self, exc_type, exc, tb): ...
