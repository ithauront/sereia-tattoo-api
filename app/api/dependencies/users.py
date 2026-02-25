from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.common import get_db
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)


# TODO Essa dependency esta marcada para ser excluida quando a refatoração para uow for completa.
def get_users_repository(db: Session = Depends(get_db)):
    return SQLAlchemyUsersRepository(db)
