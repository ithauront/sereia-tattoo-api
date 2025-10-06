from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(
    settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
