"""
Submission processing service coordinating execution workflow.
"""
import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session

from app.db_utils import get_db_session
from app.repositories.submission_repository import SubmissionRepository
from app.services.sandbox_service import SandboxService, SandboxConfig
from app.db.models import SubmissionStatus

logger = logging.getLogger(__name__)


class SubmissionProcessingService:
    """Coordinates submission processing workflow."""
    
    def __init__(self, sandbox_service: SandboxService):
        """
        Initializes service with dependencies.
        
        Args:
            sandbox_service: Sandbox service instance.
        """
        self.sandbox_service = sandbox_service
    
    def process(self, submission_data: dict, language_data: dict) -> dict:
        """
        Processes a submission through compilation and execution.
        
        Args:
            submission_data: Submission details dictionary.
            language_data: Language configuration dictionary.
            
        Returns:
            dict: Processing result with status and output.
        """
        submission_id = submission_data.get("id")
        source_code = submission_data.get("source_code", "")
        stdin = submission_data.get("stdin", "")
        
        if not all([submission_id, source_code is not None, language_data]):
            return {"error": "Invalid submission data"}
        
        with get_db_session() as db:
            repository = SubmissionRepository(db)
            
            try:
                repository.update_status(submission_id, SubmissionStatus.PROCESSING)
                
                self.sandbox_service.initialize()
                
                self.sandbox_service.prepare_source_file(
                    source_code,
                    language_data["file_name"],
                    language_data["file_extension"],
                )
                
                self.sandbox_service.prepare_stdin(stdin)
                
                if language_data.get("compile_command"):
                    compile_result = self.sandbox_service.compile(
                        language_data["compile_command"]
                    )
                    
                    if not compile_result["success"]:
                        repository.update_result(
                            submission_id=submission_id,
                            status=SubmissionStatus.ERROR,
                            stdout=compile_result["stdout"],
                            stderr=compile_result["stderr"],
                            meta=compile_result["meta"],
                        )
                        return {
                            "result": "compile_error",
                            "stdout": compile_result["stdout"],
                            "stderr": compile_result["stderr"],
                            "meta": compile_result["meta"],
                        }
                
                execution_result = self.sandbox_service.execute(
                    language_data["run_command"],
                    language_data.get("name", ""),
                )
                
                repository.update_result(
                    submission_id=submission_id,
                    status=SubmissionStatus.FINISHED,
                    stdout=execution_result["stdout"],
                    stderr=execution_result["stderr"],
                    meta=execution_result["meta"],
                )
                
                return {
                    "result": "success",
                    "stdout": execution_result["stdout"],
                    "stderr": execution_result["stderr"],
                    "meta": execution_result["meta"],
                }
                
            except Exception as e:
                logger.error(f"Error processing submission {submission_id}: {e}")
                repository.update_result(
                    submission_id=submission_id,
                    status=SubmissionStatus.ERROR,
                    stdout="",
                    stderr=str(e),
                    meta={"error": "Worker exception"},
                )
                return {"error": "Unexpected error", "details": str(e)}
                
            finally:
                self.sandbox_service.cleanup()
