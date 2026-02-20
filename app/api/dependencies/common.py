from typing import Generator
from app.infrastructure.sqlalchemy.session import SessionLocal


# TODO: aparentemente o db assim é ruim para sideeffects, estudar isso e ver como resolver.
# TODO: talvez criar um getbd read e get db write assim a gente não faz commit nas operações de read e economizamos um pouco de prcessamento
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
