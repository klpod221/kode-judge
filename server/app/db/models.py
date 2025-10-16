import enum
import uuid
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import Column, Integer, Text, DateTime, Enum, ForeignKey, Float, Boolean
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
    
    # Expected output for comparison
    expected_output = Column(Text)
    
    # Sandbox execution limits (nullable - will use defaults from config if None)
    cpu_time_limit = Column(Float)
    cpu_extra_time = Column(Float)
    wall_time_limit = Column(Float)
    memory_limit = Column(Integer)
    max_processes_and_or_threads = Column(Integer)
    max_file_size = Column(Integer)
    number_of_runs = Column(Integer)
    
    # Sandbox boolean flags (nullable - will use defaults from config if None)
    enable_per_process_and_thread_time_limit = Column(Boolean)
    enable_per_process_and_thread_memory_limit = Column(Boolean)
    redirect_stderr_to_stdout = Column(Boolean)
    enable_network = Column(Boolean)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
