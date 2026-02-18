from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.common import get_db
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)


def get_vip_clients_repository(db: Session = Depends(get_db)):
    return SQLAlchemyVipClientsRepository(db)
