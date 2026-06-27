import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.sqlalchemy.base_class import Base
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.audit_logs_repository import (
    SQLAlchemyAuditLogsRepository,
)
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

if "test" not in DATABASE_URL:
    raise RuntimeError("Tests must run against test database")


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL, future=True)

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection, future=True)
    session = SessionLocal()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def sqlalchemy_appointments_repo(
    db_session: Session,
) -> SQLAlchemyAppointmentsRepository:
    return SQLAlchemyAppointmentsRepository(session=db_session)


@pytest.fixture
def sqlalchemy_users_repo(
    db_session: Session,
) -> SQLAlchemyUsersRepository:
    return SQLAlchemyUsersRepository(session=db_session)


@pytest.fixture
def sqlalchemy_audit_logs_repo(
    db_session: Session,
) -> SQLAlchemyAuditLogsRepository:
    return SQLAlchemyAuditLogsRepository(session=db_session)
