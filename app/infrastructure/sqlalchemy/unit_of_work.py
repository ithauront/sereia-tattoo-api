from sqlalchemy.orm import Session

from app.application.studio.unit_of_work.unit_of_work import UnitOfWork
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)
from app.infrastructure.sqlalchemy.session import SessionLocal

# TODO: atualmente esse uow esta iniciando session no init. o ideal é no futuro criar um uow_read_only para usarmos em operações que não tem write
# quando tiver o de read only a gente inicia a session na def enter


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self):
        self.session: Session = SessionLocal()
        self.users = SQLAlchemyUsersRepository(self.session)
        self.vip_clients = SQLAlchemyVipClientsRepository(self.session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.rollback()
        else:
            self.commit()
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
