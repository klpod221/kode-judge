"""
Queue dependency injection for FastAPI endpoints.
"""

from typing import Generator
from redis import Redis
from rq import Queue
from app.core.config import settings


_redis_connection: Redis = None
_submission_queue: Queue = None


def get_redis_connection() -> Redis:
    """
    Provides Redis connection instance.

    Returns:
        Redis: Redis connection instance.
    """
    global _redis_connection
    if _redis_connection is None:
        _redis_connection = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    return _redis_connection


def get_submission_queue() -> Queue:
    """
    Provides submission queue instance.

    Returns:
        Queue: RQ queue instance for submissions.
    """
    global _submission_queue
    if _submission_queue is None:
        redis_conn = get_redis_connection()
        _submission_queue = Queue(
            settings.REDIS_PREFIX + "_submission_queue", connection=redis_conn
        )
    return _submission_queue
