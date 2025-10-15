import enum
import uuid
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import Column, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True)
    version = Column(Text, nullable=False)
    file_name = Column(Text, nullable=False)
    file_extension = Column(Text, nullable=False)
    compile_command = Column(Text)
    run_command = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_code = Column(Text, nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    language = relationship("Language")
    stdin = Column(Text)
    stdout = Column(Text)
    stderr = Column(Text)
    status = Column(
        Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False
    )
    meta = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
