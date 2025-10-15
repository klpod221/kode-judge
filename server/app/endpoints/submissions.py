"""
Submission endpoints for code execution and management.
"""

import uuid
from fastapi import APIRouter, Depends, Query, Response, status, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from rq import Queue

from app.dependencies.database import get_db
from app.dependencies.queue import get_submission_queue
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.language_repository import LanguageRepository
from app.services.submission_service import SubmissionService
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionRead,
    SubmissionID,
    SubmissionListResponse,
)

router = APIRouter()


def get_submission_service(
    db: AsyncSession = Depends(get_db),
) -> SubmissionService:
    """
    Provides SubmissionService instance with dependencies.

    Args:
        db: Database session from dependency injection.

    Returns:
        SubmissionService: Service instance.
    """
    submission_repo = SubmissionRepository(db)
    language_repo = LanguageRepository(db)
    queue = get_submission_queue()
    return SubmissionService(submission_repo, language_repo, queue)


@router.post(
    "/batch",
    response_model=List[SubmissionID],
    status_code=status.HTTP_201_CREATED,
    summary="Create Multiple Submissions",
    description="Creates multiple submissions at once and enqueues them for execution. Returns a list of submission IDs.",
)
async def create_batch_submissions(
    submissions: List[SubmissionCreate],
    base64_encoded: bool = Query(
        False,
        description="If true, source_code and stdin for all submissions are expected to be Base64-encoded.",
    ),
    service: SubmissionService = Depends(get_submission_service),
) -> List[SubmissionID]:
    """
    Creates multiple submissions in batch.

    Args:
        submissions: List of submission data.
        base64_encoded: Whether data is Base64 encoded.
        service: Submission service instance.

    Returns:
        List[SubmissionID]: Created submission IDs.
    """
    return await service.create_batch_submissions(submissions, base64_encoded)


@router.get(
    "/batch",
    response_model=List[SubmissionRead],
    summary="Get Multiple Submissions",
    description="Retrieves details for multiple submissions at once by providing a comma-separated list of their UUIDs.",
)
async def get_batch_submissions(
    ids: str = Query(
        ...,
        description="A comma-separated list of submission UUIDs to fetch.",
        example="uuid1,uuid2,uuid3",
    ),
    base64_encoded: bool = Query(
        False,
        description="Set to true to Base64 encode fields specified in the 'fields' parameter.",
    ),
    service: SubmissionService = Depends(get_submission_service),
) -> List[SubmissionRead]:
    """
    Retrieves multiple submissions by IDs.

    Args:
        ids: Comma-separated UUID list.
        base64_encoded: Whether to encode output as Base64.
        service: Submission service instance.

    Returns:
        List[SubmissionRead]: Submission details.
    """
    try:
        submission_ids = [uuid.UUID(sub_id.strip()) for sub_id in ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format found in 'ids' parameter.",
        )

    if not submission_ids:
        return []

    return await service.get_batch_submissions(submission_ids, base64_encoded)


@router.post(
    "/",
    response_model=None,
    summary="Create a new submission",
    description="Submits source code for execution in a specified programming language. Optionally waits for the result.",
)
async def create_submission(
    submission: SubmissionCreate,
    wait: bool = Query(
        False,
        description="If true, the endpoint will wait for the submission to be processed and return the result. Defaults to false.",
    ),
    base64_encoded: bool = Query(
        False,
        description="If true, the source_code and stdin fields are expected to be Base64-encoded. Defaults to false.",
    ),
    service: SubmissionService = Depends(get_submission_service),
):
    """
    Creates a new submission.

    Args:
        submission: Submission data.
        wait: Whether to wait for completion.
        base64_encoded: Whether data is Base64 encoded.
        service: Submission service instance.

    Returns:
        SubmissionID | SubmissionRead: Submission ID or full details.
    """
    return await service.create_submission(submission, base64_encoded, wait)


@router.get(
    "/{submission_id}",
    response_model=SubmissionRead,
    summary="Get submission details",
    description="Retrieves the current status and result of a specific submission by its UUID.",
)
async def get_submission(
    submission_id: uuid.UUID,
    base64_encoded: bool = Query(
        False,
        description="If true, the source_code, stdin, stdout, and stderr fields in the response will be Base64-encoded. Defaults to false.",
    ),
    service: SubmissionService = Depends(get_submission_service),
):
    """
    Retrieves a submission by ID.

    Args:
        submission_id: The submission identifier.
        base64_encoded: Whether to encode output as Base64.
        service: Submission service instance.

    Returns:
        SubmissionRead: Submission details.
    """
    return await service.get_submission(submission_id, base64_encoded)


@router.get(
    "/",
    response_model=SubmissionListResponse,
    summary="List all submissions",
    description="Retrieves a list of all submissions with their current statuses and results.",
)
async def list_submissions(
    base64_encoded: bool = Query(
        False,
        description="If true, the source_code, stdin, stdout, and stderr fields in the response will be Base64-encoded. Defaults to false.",
    ),
    page: int = Query(1, ge=1, description="Page number for pagination."),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page."),
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionListResponse:
    """
    Lists all submissions with pagination.

    Args:
        base64_encoded: Whether to encode output as Base64.
        page: Page number.
        page_size: Items per page.
        service: Submission service instance.

    Returns:
        SubmissionListResponse: Paginated submission list.
    """
    return await service.list_submissions(page, page_size, base64_encoded)


@router.delete(
    "/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a submission",
    description="Deletes a submission by its UUID.",
)
async def delete_submission(
    submission_id: uuid.UUID,
    service: SubmissionService = Depends(get_submission_service),
):
    """
    Deletes a submission.

    Args:
        submission_id: The submission identifier.
        service: Submission service instance.

    Returns:
        Response: Empty 204 response.
    """
    await service.delete_submission(submission_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
