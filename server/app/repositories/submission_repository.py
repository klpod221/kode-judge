"""
Repository layer for Submission entity operations.
Implements data access patterns following Repository pattern.
"""

import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.models import Submission


class SubmissionRepository:
    """Handles database operations for Submission entity."""

    def __init__(self, db: AsyncSession):
        """
        Initializes repository with database session.

        Args:
            db: Database session instance.
        """
        self.db = db

    async def create(self, submission: Submission) -> Submission:
        """
        Creates a new submission in database.

        Args:
            submission: Submission entity to create.

        Returns:
            Submission: Created submission with generated ID.
        """
        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission, ["language"])
        return submission

    async def create_many(self, submissions: List[Submission]) -> List[Submission]:
        """
        Creates multiple submissions in database.

        Args:
            submissions: List of submission entities to create.

        Returns:
            List[Submission]: Created submissions with generated IDs.
        """
        self.db.add_all(submissions)
        await self.db.commit()
        return submissions

    async def get_by_id(self, submission_id: uuid.UUID) -> Optional[Submission]:
        """
        Retrieves a submission by its ID.

        Args:
            submission_id: The unique identifier of the submission.

        Returns:
            Optional[Submission]: Submission record if found, None otherwise.
        """
        stmt = (
            select(Submission)
            .where(Submission.id == submission_id)
            .options(selectinload(Submission.language))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, submission_ids: List[uuid.UUID]) -> List[Submission]:
        """
        Retrieves multiple submissions by their IDs.

        Args:
            submission_ids: List of submission identifiers.

        Returns:
            List[Submission]: List of found submission records.
        """
        stmt = (
            select(Submission)
            .where(Submission.id.in_(submission_ids))
            .options(selectinload(Submission.language))
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_paginated(
        self, page: int, page_size: int
    ) -> Tuple[List[Submission], int]:
        """
        Retrieves paginated submissions.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            Tuple[List[Submission], int]: List of submissions and total count.
        """
        total_stmt = select(func.count()).select_from(Submission)
        total_result = await self.db.execute(total_stmt)
        total_items = total_result.scalar_one()

        stmt = (
            select(Submission)
            .options(selectinload(Submission.language))
            .order_by(Submission.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        submissions = result.scalars().all()

        return submissions, total_items

    async def delete(self, submission: Submission) -> None:
        """
        Deletes a submission from database.

        Args:
            submission: Submission entity to delete.
        """
        await self.db.delete(submission)
        await self.db.commit()
