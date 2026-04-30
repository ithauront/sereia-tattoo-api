from typing import Generator
import pytest
from sqlalchemy import StaticPool, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from app.infrastructure.sqlalchemy.base_class import Base
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.client_credit_entries_repository import (
    SQLAlchemyClientCreditEntriesRepository,
)
from app.infrastructure.sqlalchemy.repositories.payments_repository_sqlalchemy import (
    SQLAlchemyPaymentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)


@pytest.fixture
def engine() -> Generator:
    engine = create_engine(
        "sqlite:///:memory",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sql_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
def sqlalchemy_users_repo(db_session: Session) -> SQLAlchemyUsersRepository:
    return SQLAlchemyUsersRepository(session=db_session)


@pytest.fixture
def sqlalchemy_vip_clients_repo(db_session: Session) -> SQLAlchemyVipClientsRepository:
    return SQLAlchemyVipClientsRepository(session=db_session)


@pytest.fixture
def sqlalchemy_payments_repo(db_session: Session) -> SQLAlchemyPaymentsRepository:
    return SQLAlchemyPaymentsRepository(session=db_session)


@pytest.fixture
def sqlalchemy_appointments_repo(
    db_session: Session,
) -> SQLAlchemyAppointmentsRepository:
    return SQLAlchemyAppointmentsRepository(session=db_session)


@pytest.fixture
def sqlalchemy_client_credits_entries_repo(
    db_session: Session,
) -> SQLAlchemyClientCreditEntriesRepository:
    return SQLAlchemyClientCreditEntriesRepository(session=db_session)
