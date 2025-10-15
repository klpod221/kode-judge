"""
Database utilities for worker synchronous operations.
Provides session management for worker context.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.core.config import settings

SYNC_DATABASE_URL = str(settings.DATABASE_URL).replace("+asyncpg", "")

engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """
    Provides a database session context manager.
    
    Yields:
        Session: Database session instance.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
