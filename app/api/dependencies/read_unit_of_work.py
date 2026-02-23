from typing import Generator

from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.infrastructure.sqlalchemy.unit_of_work.read_unit_of_work import (
    SqlAlchemyReadUnitOfWork,
)


def get_read_unit_of_work() -> Generator[ReadUnitOfWork, None, None]:
    uow = SqlAlchemyReadUnitOfWork()
    try:
        yield uow
    finally:
        uow.session.close()
