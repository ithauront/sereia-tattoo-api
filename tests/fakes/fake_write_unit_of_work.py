from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from tests.fakes.fake_users_repository import FakeUsersRepository
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository


class FakeWriteUnitOfWork(WriteUnitOfWork):
    def __init__(self):
        self.users = FakeUsersRepository()
        self.vip_clients = FakeVipClientsRepository()
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True
