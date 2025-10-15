"""
Worker module for processing code submissions.
Refactored to follow SOLID principles with service layer architecture.
"""
import logging
from app.services.sandbox_service import SandboxService, SandboxConfig
from app.services.submission_processing_service import SubmissionProcessingService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def process_submission(submission_data: dict, language_data: dict) -> dict:
    """
    Processes a code submission through compilation and execution.
    Entry point for RQ worker jobs.
    
    Args:
        submission_data: Dictionary containing submission details.
        language_data: Dictionary containing language configuration.
        
    Returns:
        dict: Processing result with execution details.
    """
    sandbox_config = SandboxConfig()
    sandbox_service = SandboxService(sandbox_config)
    processing_service = SubmissionProcessingService(sandbox_service)
    
    return processing_service.process(submission_data, language_data)

