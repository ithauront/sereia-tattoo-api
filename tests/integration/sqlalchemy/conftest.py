from typing import Generator
from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.domain.users.entities.user import User
from app.infrastructure.sqlalchemy.base_class import Base
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)


@pytest.fixture
def engine() -> Generator:
    engine = create_engine("sqlite:///:memory", future=True)
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sqlalchemy_repo(db_session: Session) -> SQLAlchemyUsersRepository:
    return SQLAlchemyUsersRepository(session=db_session)
