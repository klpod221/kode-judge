import uuid
import asyncio
import base64

from fastapi import APIRouter, Depends, HTTPException, status, Query
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
