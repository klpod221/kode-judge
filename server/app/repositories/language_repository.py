"""
Repository layer for Language entity operations.
Implements data access patterns following Repository pattern.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import Language


class LanguageRepository:
    """Handles database operations for Language entity."""

    def __init__(self, db: AsyncSession):
        """
        Initializes repository with database session.

        Args:
            db: Database session instance.
        """
        self.db = db

    async def get_all(self) -> List[Language]:
        """
        Retrieves all languages from database.

        Returns:
            List[Language]: List of all language records.
        """
        result = await self.db.execute(select(Language))
        return result.scalars().all()

    async def get_by_id(self, language_id: int) -> Optional[Language]:
        """
        Retrieves a language by its ID.

        Args:
            language_id: The unique identifier of the language.

        Returns:
            Optional[Language]: Language record if found, None otherwise.
        """
        result = await self.db.execute(
            select(Language).where(Language.id == language_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, language_ids: List[int]) -> List[Language]:
        """
        Retrieves multiple languages by their IDs.

        Args:
            language_ids: List of language identifiers.

        Returns:
            List[Language]: List of found language records.
        """
        result = await self.db.execute(
            select(Language).where(Language.id.in_(language_ids))
        )
        return result.scalars().all()
