"""
Repository layer for worker database operations.
Implements data access patterns for updating submission results.
"""
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.db.models import Submission, SubmissionStatus


class SubmissionRepository:
    """Handles database operations for Submission entity in worker context."""
    
    def __init__(self, db: Session):
        """
        Initializes repository with database session.
        
        Args:
            db: Synchronous database session instance.
        """
        self.db = db
    
    def update_status(self, submission_id: str, status: SubmissionStatus) -> None:
        """
        Updates submission status.
        
        Args:
            submission_id: The submission identifier.
            status: New status value.
        """
        stmt = (
            update(Submission)
            .where(Submission.id == submission_id)
            .values(status=status)
        )
        self.db.execute(stmt)
        self.db.commit()
    
    def update_result(
        self,
        submission_id: str,
        status: SubmissionStatus,
        stdout: str,
        stderr: str,
        meta: dict,
    ) -> None:
        """
        Updates submission with execution results.
        
        Args:
            submission_id: The submission identifier.
            status: Final status value.
            stdout: Standard output from execution.
            stderr: Standard error from execution.
            meta: Metadata dictionary with execution details.
        """
        stmt = (
            update(Submission)
            .where(Submission.id == submission_id)
            .values(status=status, stdout=stdout, stderr=stderr, meta=meta)
        )
        self.db.execute(stmt)
        self.db.commit()
