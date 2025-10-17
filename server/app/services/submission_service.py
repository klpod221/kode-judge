"""
Service layer for Submission operations.
Implements business logic following Service pattern.
"""
import uuid
import asyncio
from typing import List, Dict, Any
from fastapi import HTTPException, status
from rq import Queue

from app.repositories.submission_repository import SubmissionRepository
from app.repositories.language_repository import LanguageRepository
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionRead,
    SubmissionID,
    SubmissionListResponse,
)
from app.schemas.language import LanguageRead
from app.db.models import Submission, SubmissionStatus
from app.utils.encoder import Base64Encoder
from app.utils.field_filter import FieldFilter


class SubmissionService:
    """Handles business logic for Submission operations."""
    
    def __init__(
        self,
        submission_repo: SubmissionRepository,
        language_repo: LanguageRepository,
        queue: Queue,
    ):
        """
        Initializes service with dependencies.
        
        Args:
            submission_repo: Submission repository instance.
            language_repo: Language repository instance.
            queue: Job queue instance.
        """
        self.submission_repo = submission_repo
        self.language_repo = language_repo
        self.queue = queue
    
    async def create_submission(
        self,
        submission_data: SubmissionCreate,
        base64_encoded: bool = False,
        wait: bool = False,
    ) -> SubmissionRead | SubmissionID:
        """
        Creates a new submission.
        
        Args:
            submission_data: Submission creation data.
            base64_encoded: Whether input is Base64 encoded.
            wait: Whether to wait for processing completion.
            
        Returns:
            SubmissionRead | SubmissionID: Full submission or just ID.
            
        Raises:
            HTTPException: If validation fails or timeout occurs.
        """
        source_code, stdin = self._decode_if_needed(
            submission_data.source_code,
            submission_data.stdin,
            base64_encoded,
        )
        
        additional_files = self._decode_additional_files(
            submission_data.additional_files,
            base64_encoded,
        )
        
        language = await self._validate_language(submission_data.language_id)
        
        db_submission = Submission(
            source_code=source_code,
            language_id=language.id,
            stdin=stdin,
            additional_files=additional_files,
            status=SubmissionStatus.PENDING,
            expected_output=submission_data.expected_output,
            cpu_time_limit=submission_data.cpu_time_limit,
            cpu_extra_time=submission_data.cpu_extra_time,
            wall_time_limit=submission_data.wall_time_limit,
            memory_limit=submission_data.memory_limit,
            max_processes_and_or_threads=submission_data.max_processes_and_or_threads,
            max_file_size=submission_data.max_file_size,
            number_of_runs=submission_data.number_of_runs,
            enable_per_process_and_thread_time_limit=submission_data.enable_per_process_and_thread_time_limit,
            enable_per_process_and_thread_memory_limit=submission_data.enable_per_process_and_thread_memory_limit,
            redirect_stderr_to_stdout=submission_data.redirect_stderr_to_stdout,
            enable_network=submission_data.enable_network,
        )
        
        created_submission = await self.submission_repo.create(db_submission)
        self._enqueue_submission(created_submission, language)
        
        if not wait:
            return SubmissionID(id=created_submission.id)
        
        return await self._wait_for_completion(created_submission)
    
    async def create_batch_submissions(
        self, submissions_data: List[SubmissionCreate], base64_encoded: bool = False
    ) -> List[SubmissionID]:
        """
        Creates multiple submissions at once.
        
        Args:
            submissions_data: List of submission creation data.
            base64_encoded: Whether inputs are Base64 encoded.
            
        Returns:
            List[SubmissionID]: List of created submission IDs.
            
        Raises:
            HTTPException: If validation fails.
        """
        language_ids = {s.language_id for s in submissions_data}
        languages = await self.language_repo.get_by_ids(list(language_ids))
        language_map = {lang.id: lang for lang in languages}
        
        new_submissions = []
        for sub_data in submissions_data:
            language = language_map.get(sub_data.language_id)
            if not language:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Language with ID {sub_data.language_id} is not supported."
                )
            
            source_code, stdin = self._decode_if_needed(
                sub_data.source_code, sub_data.stdin, base64_encoded
            )
            
            additional_files = self._decode_additional_files(
                sub_data.additional_files,
                base64_encoded,
            )
            
            db_submission = Submission(
                source_code=source_code,
                stdin=stdin,
                additional_files=additional_files,
                language_id=language.id,
                expected_output=sub_data.expected_output,
                cpu_time_limit=sub_data.cpu_time_limit,
                cpu_extra_time=sub_data.cpu_extra_time,
                wall_time_limit=sub_data.wall_time_limit,
                memory_limit=sub_data.memory_limit,
                max_processes_and_or_threads=sub_data.max_processes_and_or_threads,
                max_file_size=sub_data.max_file_size,
                number_of_runs=sub_data.number_of_runs,
                enable_per_process_and_thread_time_limit=sub_data.enable_per_process_and_thread_time_limit,
                enable_per_process_and_thread_memory_limit=sub_data.enable_per_process_and_thread_memory_limit,
                redirect_stderr_to_stdout=sub_data.redirect_stderr_to_stdout,
                enable_network=sub_data.enable_network,
            )
            db_submission.language = language
            new_submissions.append(db_submission)
        
        if not new_submissions:
            return []
        
        created_submissions = await self.submission_repo.create_many(new_submissions)
        
        for submission in created_submissions:
            self._enqueue_submission(submission, submission.language)
        
        return [SubmissionID(id=sub.id) for sub in created_submissions]
    
    async def get_submission(
        self, submission_id: uuid.UUID, base64_encoded: bool = False, fields: str | None = None
    ) -> Dict[str, Any]:
        """
        Retrieves a submission by ID.
        
        Args:
            submission_id: The submission identifier.
            base64_encoded: Whether to encode output as Base64.
            fields: Comma-separated field names to include in response.
            
        Returns:
            Dict[str, Any]: Submission data.
            
        Raises:
            HTTPException: If submission not found.
        """
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        submission_data = SubmissionRead.model_validate(submission).model_dump(
            mode="json"
        )
        
        if base64_encoded:
            submission_data = self._encode_submission_data(submission, submission_data)
        
        field_set = FieldFilter.parse_fields(fields)
        submission_data = FieldFilter.filter_data(submission_data, field_set)
        
        return submission_data
    
    async def get_batch_submissions(
        self, submission_ids: List[uuid.UUID], base64_encoded: bool = False, fields: str | None = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves multiple submissions by IDs.
        
        Args:
            submission_ids: List of submission identifiers.
            base64_encoded: Whether to encode output as Base64.
            fields: Comma-separated field names to include in response.
            
        Returns:
            List[Dict[str, Any]]: List of submission data.
        """
        submissions = await self.submission_repo.get_by_ids(submission_ids)
        submissions_data = [
            SubmissionRead.model_validate(sub).model_dump(mode="json") 
            for sub in submissions
        ]
        
        if base64_encoded:
            for submission_data, db_submission in zip(submissions_data, submissions):
                self._encode_dict_fields(submission_data, db_submission)
        
        field_set = FieldFilter.parse_fields(fields)
        submissions_data = FieldFilter.filter_list(submissions_data, field_set)
        
        return submissions_data
    
    async def list_submissions(
        self, page: int, page_size: int, base64_encoded: bool = False, fields: str | None = None
    ) -> Dict[str, Any]:
        """
        Retrieves paginated list of submissions.
        
        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            base64_encoded: Whether to encode output as Base64.
            fields: Comma-separated field names to include in response.
            
        Returns:
            Dict[str, Any]: Paginated submission list.
        """
        submissions, total_items = await self.submission_repo.get_paginated(
            page, page_size
        )
        
        submissions_data = [
            SubmissionRead.model_validate(sub).model_dump(mode="json")
            for sub in submissions
        ]
        
        if base64_encoded:
            for submission_data, db_submission in zip(submissions_data, submissions):
                self._encode_dict_fields(submission_data, db_submission)
        
        field_set = FieldFilter.parse_fields(fields)
        submissions_data = FieldFilter.filter_list(submissions_data, field_set)
        
        total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 1
        
        return {
            "items": submissions_data,
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
        }
    
    async def delete_submission(self, submission_id: uuid.UUID) -> None:
        """
        Deletes a submission by ID.
        
        Args:
            submission_id: The submission identifier.
            
        Raises:
            HTTPException: If submission not found.
        """
        submission = await self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        await self.submission_repo.delete(submission)
    
    def _decode_if_needed(
        self, source_code: str, stdin: str | None, base64_encoded: bool
    ) -> tuple[str, str | None]:
        """
        Decodes Base64 encoded data if needed.
        
        Args:
            source_code: Source code (possibly encoded).
            stdin: Standard input (possibly encoded).
            base64_encoded: Whether data is encoded.
            
        Returns:
            tuple[str, str | None]: Decoded source code and stdin.
            
        Raises:
            HTTPException: If decoding fails.
        """
        if not base64_encoded:
            return source_code, stdin
        
        try:
            decoded_source = Base64Encoder.decode(source_code)
            decoded_stdin = Base64Encoder.decode_optional(stdin)
            return decoded_source, decoded_stdin
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    def _decode_additional_files(
        self, additional_files: List[Dict[str, Any]] | None, base64_encoded: bool
    ) -> List[Dict[str, Any]] | None:
        """
        Decodes additional files content if Base64 encoded.
        
        Args:
            additional_files: List of files with name and content.
            base64_encoded: Whether content is Base64 encoded.
            
        Returns:
            List[Dict[str, Any]] | None: Decoded files or None.
            
        Raises:
            HTTPException: If decoding fails.
        """
        if not additional_files or not base64_encoded:
            return additional_files
        
        try:
            decoded_files = []
            for file in additional_files:
                decoded_file = {
                    "name": file.get("name"),
                    "content": Base64Encoder.decode(file.get("content", ""))
                }
                decoded_files.append(decoded_file)
            return decoded_files
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Base64 in additional_files: {e}"
            )
    
    async def _validate_language(self, language_id: int):
        """
        Validates that a language exists.
        
        Args:
            language_id: The language identifier.
            
        Returns:
            Language: The language entity.
            
        Raises:
            HTTPException: If language not found.
        """
        language = await self.language_repo.get_by_id(language_id)
        if not language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Language with ID {language_id} is not supported."
            )
        return language
    
    def _enqueue_submission(self, submission: Submission, language) -> None:
        """
        Enqueues a submission for processing.
        
        Args:
            submission: Submission entity.
            language: Language entity.
        """
        submission_data = SubmissionRead.model_validate(submission).model_dump(
            mode="json"
        )
        language_data = LanguageRead.model_validate(language).model_dump(mode="json")
        self.queue.enqueue("app.worker.process_submission", submission_data, language_data)
    
    async def _wait_for_completion(
        self, submission: Submission, timeout: int = 15, poll_interval: float = 0.5
    ) -> SubmissionRead:
        """
        Waits for submission processing to complete.
        
        Args:
            submission: Submission entity.
            timeout: Maximum wait time in seconds.
            poll_interval: Time between status checks.
            
        Returns:
            SubmissionRead: Completed submission.
            
        Raises:
            HTTPException: If timeout occurs.
        """
        elapsed_time = 0.0
        
        while elapsed_time < timeout:
            refreshed = await self.submission_repo.get_by_id(submission.id)
            
            if refreshed and refreshed.status in {SubmissionStatus.FINISHED, SubmissionStatus.ERROR}:
                return SubmissionRead.model_validate(refreshed)
            
            await asyncio.sleep(poll_interval)
            elapsed_time += poll_interval
        
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Request timed out while waiting for submission to complete."
        )
    
    def _encode_submission_data(
        self, submission: Submission, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Encodes submission fields to Base64.
        
        Args:
            submission: Submission entity.
            data: Submission data dictionary.
            
        Returns:
            Dict[str, Any]: Data with encoded fields.
        """
        data["source_code"] = Base64Encoder.encode(submission.source_code)
        data["stdin"] = Base64Encoder.encode_optional(submission.stdin)
        data["stdout"] = Base64Encoder.encode_optional(submission.stdout)
        data["stderr"] = Base64Encoder.encode_optional(submission.stderr)
        
        if submission.additional_files:
            encoded_files = []
            for file in submission.additional_files:
                encoded_file = {
                    "name": file.get("name"),
                    "content": Base64Encoder.encode(file.get("content", ""))
                }
                encoded_files.append(encoded_file)
            data["additional_files"] = encoded_files
        
        return data
    
    def _encode_submission_fields(
        self, submission_schema, submission_entity: Submission
    ) -> None:
        """
        Encodes submission schema fields in-place.
        
        Args:
            submission_schema: Submission schema instance.
            submission_entity: Submission entity.
        """
        submission_schema.source_code = Base64Encoder.encode(
            submission_entity.source_code
        )
        submission_schema.stdin = Base64Encoder.encode_optional(submission_entity.stdin)
        submission_schema.stdout = Base64Encoder.encode_optional(
            submission_entity.stdout
        )
        submission_schema.stderr = Base64Encoder.encode_optional(
            submission_entity.stderr
        )
        
        if submission_entity.additional_files:
            encoded_files = []
            for file in submission_entity.additional_files:
                encoded_file = {
                    "name": file.get("name"),
                    "content": Base64Encoder.encode(file.get("content", ""))
                }
                encoded_files.append(encoded_file)
            submission_schema.additional_files = encoded_files
    
    def _encode_dict_fields(
        self, data: Dict[str, Any], submission: Submission
    ) -> None:
        """
        Encodes dictionary fields in-place.
        
        Args:
            data: Data dictionary.
            submission: Submission entity.
        """
        data["source_code"] = Base64Encoder.encode(submission.source_code)
        data["stdin"] = Base64Encoder.encode_optional(submission.stdin)
        data["stdout"] = Base64Encoder.encode_optional(submission.stdout)
        data["stderr"] = Base64Encoder.encode_optional(submission.stderr)
        
        if submission.additional_files:
            encoded_files = []
            for file in submission.additional_files:
                encoded_file = {
                    "name": file.get("name"),
                    "content": Base64Encoder.encode(file.get("content", ""))
                }
                encoded_files.append(encoded_file)
            data["additional_files"] = encoded_files
