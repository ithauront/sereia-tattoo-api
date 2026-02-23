from sqlalchemy.orm import Session

from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)
from app.infrastructure.sqlalchemy.session import SessionLocal


class SqlAlchemyReadUnitOfWork(ReadUnitOfWork):
    def __init__(self):
        self.session: Session = SessionLocal()
        self.users = SQLAlchemyUsersRepository(self.session)
        self.vip_clients = SQLAlchemyVipClientsRepository(self.session)

    def __exit__(self, exc_type, exc, tb):
        pass
