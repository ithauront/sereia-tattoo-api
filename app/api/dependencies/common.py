from typing import Generator
from app.infrastructure.sqlalchemy.session import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
