"""
Submission processing service coordinating execution workflow.
"""
import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db_utils import get_db_session
from app.repositories.submission_repository import SubmissionRepository
from app.services.sandbox_service import SandboxService, SandboxConfig
from app.db.models import SubmissionStatus
from app.core.config import settings

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
    
    def _build_sandbox_config(self, submission_data: dict) -> SandboxConfig:
        """
        Builds sandbox configuration from submission data with fallback to settings.
        
        Args:
            submission_data: Submission details dictionary.
            
        Returns:
            SandboxConfig: Configuration for sandbox execution.
        """
        return SandboxConfig(
            cpu_time_limit=submission_data.get("cpu_time_limit") or settings.SANDBOX_CPU_TIME_LIMIT,
            cpu_extra_time=submission_data.get("cpu_extra_time") or settings.SANDBOX_CPU_EXTRA_TIME,
            wall_time_limit=submission_data.get("wall_time_limit") or settings.SANDBOX_WALL_TIME_LIMIT,
            memory_limit=submission_data.get("memory_limit") or settings.SANDBOX_MEMORY_LIMIT,
            max_processes=submission_data.get("max_processes_and_or_threads") or settings.SANDBOX_MAX_PROCESSES,
            max_file_size=submission_data.get("max_file_size") or settings.SANDBOX_MAX_FILE_SIZE,
            enable_per_process_time_limit=submission_data.get("enable_per_process_and_thread_time_limit") 
                if submission_data.get("enable_per_process_and_thread_time_limit") is not None 
                else settings.SANDBOX_ENABLE_PER_PROCESS_TIME_LIMIT,
            enable_per_process_memory_limit=submission_data.get("enable_per_process_and_thread_memory_limit") 
                if submission_data.get("enable_per_process_and_thread_memory_limit") is not None 
                else settings.SANDBOX_ENABLE_PER_PROCESS_MEMORY_LIMIT,
            redirect_stderr_to_stdout=submission_data.get("redirect_stderr_to_stdout") 
                if submission_data.get("redirect_stderr_to_stdout") is not None 
                else settings.SANDBOX_REDIRECT_STDERR_TO_STDOUT,
            enable_network=submission_data.get("enable_network") 
                if submission_data.get("enable_network") is not None 
                else settings.SANDBOX_ENABLE_NETWORK,
        )
    
    def _execute_multiple_runs(
        self, run_command: str, language_name: str, number_of_runs: int
    ) -> Dict[str, Any]:
        """
        Executes code multiple times and returns averaged results.
        
        Args:
            run_command: Shell command for execution.
            language_name: Name of programming language.
            number_of_runs: Number of times to run the code.
            
        Returns:
            Dict[str, Any]: Execution result with averaged metrics.
        """
        total_time = 0.0
        total_memory = 0.0
        last_result = None
        
        for run_num in range(number_of_runs):
            logger.info(f"Execution run {run_num + 1}/{number_of_runs}")
            result = self.sandbox_service.execute(run_command, language_name)
            last_result = result
            
            if result["meta"].get("time"):
                total_time += float(result["meta"]["time"])
            if result["meta"].get("max-rss"):
                total_memory += float(result["meta"]["max-rss"])
        
        if last_result and number_of_runs > 1:
            last_result["meta"]["avg_time"] = str(total_time / number_of_runs)
            last_result["meta"]["avg_memory"] = str(total_memory / number_of_runs)
            last_result["meta"]["total_runs"] = str(number_of_runs)
        
        return last_result
    
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
        expected_output = submission_data.get("expected_output")
        number_of_runs = submission_data.get("number_of_runs") or settings.SANDBOX_NUMBER_OF_RUNS
        
        if not all([submission_id, source_code is not None, language_data]):
            return {"error": "Invalid submission data"}
        
        with get_db_session() as db:
            repository = SubmissionRepository(db)
            
            try:
                repository.update_status(submission_id, SubmissionStatus.PROCESSING)
                
                sandbox_config = self._build_sandbox_config(submission_data)
                self.sandbox_service.config = sandbox_config
                
                self.sandbox_service.initialize()
                
                # Prepare main source file
                self.sandbox_service.prepare_source_file(
                    source_code,
                    language_data["file_name"],
                    language_data["file_extension"],
                )

                # Prepare additional files (if any)
                try:
                    additional_files = submission_data.get("additional_files") or []
                    self.sandbox_service.prepare_additional_files(additional_files)
                except ValueError as ve:
                    repository.update_result(
                        submission_id=submission_id,
                        status=SubmissionStatus.ERROR,
                        stdout="",
                        stderr=str(ve),
                        meta={"error": "additional_files_validation"},
                    )
                    return {"error": "additional_files_validation", "details": str(ve)}

                # Prepare stdin
                self.sandbox_service.prepare_stdin(stdin)
                
                compile_output = None
                if language_data.get("compile_command"):
                    compile_result = self.sandbox_service.compile(
                        language_data["compile_command"]
                    )
                    
                    # Combine stdout and stderr for compile_output
                    compile_output = f"{compile_result['stdout']}\n{compile_result['stderr']}".strip()
                    
                    if not compile_result["success"]:
                        repository.update_result(
                            submission_id=submission_id,
                            status=SubmissionStatus.ERROR,
                            stdout=compile_result["stdout"],
                            stderr=compile_result["stderr"],
                            compile_output=compile_output,
                            meta=compile_result["meta"],
                        )
                        return {
                            "result": "compile_error",
                            "stdout": compile_result["stdout"],
                            "stderr": compile_result["stderr"],
                            "compile_output": compile_output,
                            "meta": compile_result["meta"],
                        }
                
                execution_result = self._execute_multiple_runs(
                    language_data["run_command"],
                    language_data.get("name", ""),
                    number_of_runs,
                )
                
                if expected_output is not None:
                    actual_output = execution_result["stdout"].strip()
                    expected = expected_output.strip()
                    execution_result["meta"]["output_matched"] = str(actual_output == expected)
                
                repository.update_result(
                    submission_id=submission_id,
                    status=SubmissionStatus.FINISHED,
                    stdout=execution_result["stdout"],
                    stderr=execution_result["stderr"],
                    compile_output=compile_output,
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
