from typing import Generator

from app.infrastructure.sqlalchemy.unit_of_work.write_unit_of_work import (
    SqlAlchemyWriteUnitOfWork,
)


def get_write_unit_of_work() -> Generator[SqlAlchemyWriteUnitOfWork, None, None]:
    uow = SqlAlchemyWriteUnitOfWork()
    try:
        yield uow
    finally:
        uow.session.close()
