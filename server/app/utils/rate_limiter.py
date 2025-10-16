"""
Rate limiter implementation using Redis for distributed rate limiting.
"""

import time
from typing import Optional
from redis import Redis
from app.core.config import settings


class RateLimiter:
    """
    Handles rate limiting logic using Redis as the backend storage.
    Supports both fixed-window and sliding-window strategies.
    """

    def __init__(self, redis_client: Redis):
        """
        Initializes the rate limiter.

        Args:
            redis_client: Redis client instance.
        """
        self.redis = redis_client
        self.prefix = f"{settings.REDIS_PREFIX}:ratelimit"

    def _get_fixed_window_key(self, identifier: str, window: int) -> str:
        """
        Generates a Redis key for fixed-window strategy.

        Args:
            identifier: Unique identifier (e.g., IP address, user ID).
            window: Time window in seconds.

        Returns:
            str: Redis key.
        """
        current_window = int(time.time() / window)
        return f"{self.prefix}:fixed:{identifier}:{window}:{current_window}"

    def _get_sliding_window_key(self, identifier: str, window: int) -> str:
        """
        Generates a Redis key for sliding-window strategy.

        Args:
            identifier: Unique identifier.
            window: Time window in seconds.

        Returns:
            str: Redis key.
        """
        return f"{self.prefix}:sliding:{identifier}:{window}"

    def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int,
        strategy: str = "fixed-window",
    ) -> tuple[bool, dict]:
        """
        Checks if the rate limit has been exceeded.

        Args:
            identifier: Unique identifier for the requester.
            limit: Maximum number of requests allowed.
            window: Time window in seconds.
            strategy: Rate limiting strategy ('fixed-window' or 'sliding-window').

        Returns:
            tuple[bool, dict]: (is_allowed, rate_limit_info)
                - is_allowed: True if request is allowed, False otherwise.
                - rate_limit_info: Dictionary with limit, remaining, reset info.
        """
        if strategy == "sliding-window":
            return self._check_sliding_window(identifier, limit, window)
        else:
            return self._check_fixed_window(identifier, limit, window)

    def _check_fixed_window(
        self, identifier: str, limit: int, window: int
    ) -> tuple[bool, dict]:
        """
        Implements fixed-window rate limiting.

        Args:
            identifier: Unique identifier.
            limit: Request limit.
            window: Time window in seconds.

        Returns:
            tuple[bool, dict]: Rate limit result.
        """
        key = self._get_fixed_window_key(identifier, window)
        
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        current_count, _ = pipe.execute()

        current_window_start = int(time.time() / window) * window
        reset_time = current_window_start + window

        is_allowed = current_count <= limit
        remaining = max(0, limit - current_count)

        return is_allowed, {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": reset_time - int(time.time()) if not is_allowed else None,
        }

    def _check_sliding_window(
        self, identifier: str, limit: int, window: int
    ) -> tuple[bool, dict]:
        """
        Implements sliding-window rate limiting using sorted sets.

        Args:
            identifier: Unique identifier.
            limit: Request limit.
            window: Time window in seconds.

        Returns:
            tuple[bool, dict]: Rate limit result.
        """
        key = self._get_sliding_window_key(identifier, window)
        current_time = time.time()
        window_start = current_time - window

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, window)
        _, current_count, _, _ = pipe.execute()

        is_allowed = current_count < limit
        remaining = max(0, limit - current_count - 1)

        oldest_timestamp = None
        if not is_allowed:
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_timestamp = oldest[0][1]

        reset_time = int(oldest_timestamp + window) if oldest_timestamp else int(current_time + window)
        retry_after = reset_time - int(current_time) if not is_allowed else None

        return is_allowed, {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": retry_after,
        }

    def reset_rate_limit(self, identifier: str) -> None:
        """
        Resets rate limit for a specific identifier.

        Args:
            identifier: Unique identifier to reset.
        """
        pattern = f"{self.prefix}:*:{identifier}:*"
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)
