from abc import ABC

from app.application.studio.repositories.client_credit_entries_repository import (
    ClientCreditEntriesRepository,
)
from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.repositories.vip_clients_repository import (
    VipClientsRepository,
)


class BaseUnitOfWork(ABC):
    users: UsersRepository
    vip_clients: VipClientsRepository
    client_credit_entries: ClientCreditEntriesRepository
