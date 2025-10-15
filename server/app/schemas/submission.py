import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from app.db.models import SubmissionStatus
from typing import Optional, Dict, Any, List

from .language import LanguageShow


class SubmissionBase(BaseModel):
    source_code: str
    language_id: int
    stdin: str | None = None


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionID(BaseModel):
    id: uuid.UUID


class SubmissionRead(SubmissionBase):
    id: uuid.UUID
    language: LanguageShow
    status: SubmissionStatus
    stdout: str | None
    stderr: str | None
    meta: Dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    items: list["SubmissionRead"]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int
