import uuid
from pydantic import BaseModel
from datetime import datetime
from app.db.models import SubmissionStatus
from typing import Dict, Any

from .language import LanguageRead

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
    language: LanguageRead
    status: SubmissionStatus
    stdout: str | None
    stderr: str | None
    meta: Dict[str, Any] | None
    created_at: datetime
    
    class Config:
        from_attributes = True