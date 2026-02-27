from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from tests.fakes.fake_users_repository import FakeUsersRepository
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository


class FakeReadUnitOfWork(ReadUnitOfWork):
    def __init__(self):
        self.users = FakeUsersRepository()
        self.vip_clients = FakeVipClientsRepository()

    def __exit__(self, exc_type, exc, tb):
        pass
