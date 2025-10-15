"""
Application state management.
Stores global application state like start time.
"""
import time

# Application start time
APP_START_TIME = time.time()


def get_app_start_time() -> float:
    """
    Gets the application start time.
    
    Returns:
        float: Unix timestamp of application start.
    """
    return APP_START_TIME
