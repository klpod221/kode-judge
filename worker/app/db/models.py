import enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    source_code = Column(Text, nullable=False)
    language_id = Column(Integer, nullable=False)
    stdin = Column(Text)
    stdout = Column(Text)
    stderr = Column(Text)
    status = Column(
        Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False
    )
    meta = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    version = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_extension = Column(String, nullable=False)
    compile_command = Column(Text)
    run_command = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    