from abc import ABC

from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.repositories.vip_clients_repository import (
    VipClientsRepository,
)


class BaseUnitOfWork(ABC):
    users: UsersRepository
    vip_clients: VipClientsRepository
