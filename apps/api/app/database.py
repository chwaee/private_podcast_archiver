"""SQLAlchemy setup.

Engine + session factory. Base is defined here and re-exported/used by models (M1+).
All models must include workspace_id for isolation (enforced in queries from M1 onward).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import DATABASE_URL, APP_ENV

# Echo SQL in development for visibility
echo = APP_ENV == "development"

engine = create_engine(DATABASE_URL, echo=echo, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base for all ORM models (M1+)."""
    pass


def get_db():
    """FastAPI dependency for DB session (used from M1 onward)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
