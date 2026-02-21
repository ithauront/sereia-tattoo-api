from typing import Generator
import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.infrastructure.sqlalchemy.base_class import Base
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
    transaction.rollback()
    connection.close()


@pytest.fixture
def sqlalchemy_users_repo(db_session: Session) -> SQLAlchemyUsersRepository:
    return SQLAlchemyUsersRepository(session=db_session)


@pytest.fixture
def sqlalchemy_vip_clients_repo(db_session: Session) -> SQLAlchemyVipClientsRepository:
    return SQLAlchemyVipClientsRepository(session=db_session)
