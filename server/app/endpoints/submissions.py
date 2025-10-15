import uuid
import asyncio
import base64

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from redis import Redis
from rq import Queue

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionRead,
    SubmissionID,
    SubmissionListResponse,
)
from app.schemas.language import LanguageRead
from app.db import models
from app.db.models import SubmissionStatus

router = APIRouter()

redis_conn = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
submission_queue = Queue(
    settings.REDIS_PREFIX + "_submission_queue", connection=redis_conn
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


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
    db: AsyncSession = Depends(get_db),
):
    language_ids = {s.language_id for s in submissions}
    lang_result = await db.execute(
        select(models.Language).where(models.Language.id.in_(language_ids))
    )
    valid_languages = {lang.id: lang for lang in lang_result.scalars().all()}

    new_db_submissions = []
    for sub_create in submissions:
        language = valid_languages.get(sub_create.language_id)
        if not language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Language with ID {sub_create.language_id} is not supported in this batch.",
            )

        source_code = sub_create.source_code
        stdin = sub_create.stdin
        if base64_encoded:
            try:
                source_code = base64.b64decode(source_code).decode("utf-8")
                if stdin:
                    stdin = base64.b64decode(stdin).decode("utf-8")
            except (ValueError, TypeError, base64.binascii.Error) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid Base64 data in batch for submission with language ID {sub_create.language_id}: {e}",
                )

        db_submission = models.Submission(
            source_code=source_code, stdin=stdin, language_id=language.id
        )
        db_submission.language = language
        new_db_submissions.append(db_submission)

    if not new_db_submissions:
        return []

    db.add_all(new_db_submissions)
    await db.commit()

    for db_sub in new_db_submissions:
        submission_data = SubmissionRead.model_validate(db_sub).model_dump(mode="json")
        language_data = LanguageRead.model_validate(db_sub.language).model_dump(
            mode="json"
        )
        submission_queue.enqueue(
            "app.worker.process_submission", submission_data, language_data
        )

    return [SubmissionID(id=sub.id) for sub in new_db_submissions]


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
    db: AsyncSession = Depends(get_db),
):
    try:
        submission_ids = [uuid.UUID(sub_id.strip()) for sub_id in ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format found in 'ids' parameter.",
        )

    if not submission_ids:
        return []

    stmt = (
        select(models.Submission)
        .where(models.Submission.id.in_(submission_ids))
        .options(selectinload(models.Submission.language))
    )
    result = await db.execute(stmt)
    db_submissions = result.scalars().all()

    response_data = [SubmissionRead.model_validate(sub) for sub in db_submissions]

    if base64_encoded:
        for submission, db_submission in zip(response_data, db_submissions):
            submission.source_code = base64.b64encode(
                db_submission.source_code.encode("utf-8")
            ).decode("utf-8")
            if db_submission.stdin:
                submission.stdin = base64.b64encode(
                    db_submission.stdin.encode("utf-8")
                ).decode("utf-8")
            if db_submission.stdout:
                submission.stdout = base64.b64encode(
                    db_submission.stdout.encode("utf-8")
                ).decode("utf-8")
            if db_submission.stderr:
                submission.stderr = base64.b64encode(
                    db_submission.stderr.encode("utf-8")
                ).decode("utf-8")

    return response_data


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
    db: AsyncSession = Depends(get_db),
):
    if base64_encoded:
        try:
            submission.source_code = base64.b64decode(submission.source_code).decode(
                "utf-8"
            )
            if submission.stdin:
                submission.stdin = base64.b64decode(submission.stdin).decode("utf-8")
        except (ValueError, TypeError, base64.binascii.Error) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Base64 data: {e}",
            )

    # Find the language
    lang_result = await db.execute(
        select(models.Language).where(models.Language.id == submission.language_id)
    )
    language = lang_result.scalars().first()

    if not language:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language with ID {submission.language_id} is not supported.",
        )

    db_submission = models.Submission(
        source_code=submission.source_code,
        language_id=submission.language_id,
        stdin=submission.stdin,
        status=SubmissionStatus.PENDING,
    )
    db.add(db_submission)
    await db.commit()
    await db.refresh(db_submission, ["language"])

    submission_data = SubmissionRead.model_validate(db_submission).model_dump(
        mode="json"
    )
    language_data = LanguageRead.model_validate(language).model_dump(mode="json")
    submission_queue.enqueue(
        "app.worker.process_submission", submission_data, language_data
    )

    if not wait:
        return SubmissionID(id=db_submission.id)

    timeout = 15  # seconds
    poll_interval = 0.5  # seconds
    elapsed_time = 0.0

    while elapsed_time < timeout:
        await db.refresh(db_submission)

        if db_submission.status in {SubmissionStatus.FINISHED, SubmissionStatus.ERROR}:
            return db_submission

        await asyncio.sleep(poll_interval)
        elapsed_time += poll_interval

    raise HTTPException(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        detail="Request timed out while waiting for submission to complete.",
    )


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
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(models.Submission)
        .where(models.Submission.id == submission_id)
        .options(selectinload(models.Submission.language))
    )

    result = await db.execute(stmt)
    db_submission = result.scalars().first()

    if not db_submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    submission_data = SubmissionRead.model_validate(db_submission).model_dump(
        mode="json"
    )

    if base64_encoded:
        submission_data["source_code"] = base64.b64encode(
            db_submission.source_code.encode("utf-8")
        ).decode("utf-8")
        if db_submission.stdin:
            submission_data["stdin"] = base64.b64encode(
                db_submission.stdin.encode("utf-8")
            ).decode("utf-8")
        if db_submission.stdout:
            submission_data["stdout"] = base64.b64encode(
                db_submission.stdout.encode("utf-8")
            ).decode("utf-8")
        if db_submission.stderr:
            submission_data["stderr"] = base64.b64encode(
                db_submission.stderr.encode("utf-8")
            ).decode("utf-8")

    return submission_data


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
    db: AsyncSession = Depends(get_db),
):

    # Get total items for pagination
    total_stmt = select(func.count()).select_from(models.Submission)
    total_result = await db.execute(total_stmt)
    total_items = total_result.scalar_one()

    stmt = (
        select(models.Submission)
        .options(selectinload(models.Submission.language))
        .order_by(models.Submission.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    db_submissions = result.scalars().all()

    submissions_data = [
        SubmissionRead.model_validate(submission).model_dump(mode="json")
        for submission in db_submissions
    ]

    if base64_encoded:
        for submission, db_submission in zip(submissions_data, db_submissions):
            submission["source_code"] = base64.b64encode(
                db_submission.source_code.encode("utf-8")
            ).decode("utf-8")
            if db_submission.stdin:
                submission["stdin"] = base64.b64encode(
                    db_submission.stdin.encode("utf-8")
                ).decode("utf-8")
            if db_submission.stdout:
                submission["stdout"] = base64.b64encode(
                    db_submission.stdout.encode("utf-8")
                ).decode("utf-8")
            if db_submission.stderr:
                submission["stderr"] = base64.b64encode(
                    db_submission.stderr.encode("utf-8")
                ).decode("utf-8")

    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 1

    return {
        "items": submissions_data,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
    }


@router.delete(
    "/{submission_id}",
    status_code=204,
    summary="Delete a submission",
    description="Deletes a submission by its UUID.",
)
async def delete_submission(
    submission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(models.Submission).where(models.Submission.id == submission_id)
    result = await db.execute(stmt)
    db_submission = result.scalars().first()

    if not db_submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )

    await db.delete(db_submission)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
