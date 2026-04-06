from sqlalchemy.orm import Session

from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.infrastructure.sqlalchemy.repositories.client_credit_entries_repository import SQLAlchemyClientCreditEntriesRepository
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)
from app.infrastructure.sqlalchemy.session import SessionLocal


class SqlAlchemyWriteUnitOfWork(WriteUnitOfWork):
    def __init__(self):
        self.session: Session = SessionLocal()
        self.users = SQLAlchemyUsersRepository(self.session)
        self.vip_clients = SQLAlchemyVipClientsRepository(self.session)
        self.client_credit_entries = SQLAlchemyClientCreditEntriesRepository(self.session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
