import uuid
from pydantic import BaseModel, Field, model_serializer, field_validator
from datetime import datetime
from app.db.models import SubmissionStatus
from typing import Optional, Dict, Any, List
from app.core.config import settings

from .language import LanguageShow


class SubmissionBase(BaseModel):
    source_code: str = Field(..., min_length=1, description="Source code for the submission (cannot be empty)")
    language_id: int
    stdin: str | None = None
    additional_files: list[dict] | None = None
    
    expected_output: str | None = None
    
    cpu_time_limit: float | None = Field(None, gt=0)
    cpu_extra_time: float | None = Field(None, gt=0)
    wall_time_limit: float | None = Field(None, gt=0)
    memory_limit: int | None = Field(None, gt=0)
    max_processes_and_or_threads: int | None = Field(None, gt=0)
    max_file_size: int | None = Field(None, gt=0)
    number_of_runs: int | None = Field(None, gt=0)
    
    enable_per_process_and_thread_time_limit: bool | None = None
    enable_per_process_and_thread_memory_limit: bool | None = None
    redirect_stderr_to_stdout: bool | None = None
    enable_network: bool | None = None
    
    @field_validator('source_code')
    @classmethod
    def validate_source_code(cls, v: str) -> str:
        """
        Validates source code is not just whitespace.
        
        Args:
            v: Source code string.
            
        Returns:
            str: Validated source code.
            
        Raises:
            ValueError: If source code is only whitespace.
        """
        if not v or not v.strip():
            raise ValueError('Source code cannot be empty or contain only whitespace')
        return v


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
    compile_output: str | None
    meta: Dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True
    
    @model_serializer
    def serialize_with_defaults(self) -> Dict[str, Any]:
        """
        Serializes model with default values for null sandbox parameters.
        """
        data = {
            'id': str(self.id),
            'source_code': self.source_code,
            'language_id': self.language_id,
            'stdin': self.stdin,
            'additional_files': self.additional_files,
            'language': self.language,
            'status': self.status,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'compile_output': self.compile_output,
            'meta': self.meta,
            'created_at': self.created_at,
            
            # Fill null values with defaults from config
            'expected_output': self.expected_output,
            'cpu_time_limit': self.cpu_time_limit if self.cpu_time_limit is not None else settings.SANDBOX_CPU_TIME_LIMIT,
            'cpu_extra_time': self.cpu_extra_time if self.cpu_extra_time is not None else settings.SANDBOX_CPU_EXTRA_TIME,
            'wall_time_limit': self.wall_time_limit if self.wall_time_limit is not None else settings.SANDBOX_WALL_TIME_LIMIT,
            'memory_limit': self.memory_limit if self.memory_limit is not None else settings.SANDBOX_MEMORY_LIMIT,
            'max_processes_and_or_threads': self.max_processes_and_or_threads if self.max_processes_and_or_threads is not None else settings.SANDBOX_MAX_PROCESSES,
            'max_file_size': self.max_file_size if self.max_file_size is not None else settings.SANDBOX_MAX_FILE_SIZE,
            'number_of_runs': self.number_of_runs if self.number_of_runs is not None else settings.SANDBOX_NUMBER_OF_RUNS,
            'enable_per_process_and_thread_time_limit': self.enable_per_process_and_thread_time_limit if self.enable_per_process_and_thread_time_limit is not None else settings.SANDBOX_ENABLE_PER_PROCESS_TIME_LIMIT,
            'enable_per_process_and_thread_memory_limit': self.enable_per_process_and_thread_memory_limit if self.enable_per_process_and_thread_memory_limit is not None else settings.SANDBOX_ENABLE_PER_PROCESS_MEMORY_LIMIT,
            'redirect_stderr_to_stdout': self.redirect_stderr_to_stdout if self.redirect_stderr_to_stdout is not None else settings.SANDBOX_REDIRECT_STDERR_TO_STDOUT,
            'enable_network': self.enable_network if self.enable_network is not None else settings.SANDBOX_ENABLE_NETWORK,
        }
        return data


class SubmissionListResponse(BaseModel):
    items: list["SubmissionRead"]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int
