"""
Application state management.
Stores global application state like start time.
"""
import time

# Application start time
APP_START_TIME = time.time()
# Application version
APP_VERSION = "1.0.0"


def get_app_start_time() -> float:
    """
    Gets the application start time.
    
    Returns:
        float: Unix timestamp of application start.
    """
    return APP_START_TIME

def get_app_version() -> str:
    """
    Gets the application version.
    
    Returns:
        str: Application version string.
    """
    return APP_VERSION
