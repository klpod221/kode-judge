"""
Database dependency injection for FastAPI endpoints.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session for dependency injection.

    Yields:
        AsyncSession: Database session instance.
    """
    async with AsyncSessionLocal() as session:
        yield session
