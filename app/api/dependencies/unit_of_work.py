from typing import Generator

from app.infrastructure.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


def get_unit_of_work() -> Generator[SqlAlchemyUnitOfWork, None, None]:
    uow = SqlAlchemyUnitOfWork()
    try:
        yield uow
    finally:
        uow.session.close()
