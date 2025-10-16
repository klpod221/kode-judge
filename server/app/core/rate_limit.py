"""
Rate limiting middleware for FastAPI application.
"""

import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from redis import Redis
from app.core.config import settings
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting on incoming requests.
    """

    def __init__(self, app, redis_client: Redis):
        """
        Initializes the rate limit middleware.

        Args:
            app: FastAPI application instance.
            redis_client: Redis client for rate limiting.
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(redis_client)
        self.enabled = settings.RATE_LIMIT_ENABLED

    def _get_client_identifier(self, request: Request) -> str:
        """
        Extracts a unique identifier for the client.

        Args:
            request: Incoming HTTP request.

        Returns:
            str: Client identifier (IP address or authenticated user ID).
        """
        # Priority: authenticated user ID > forwarded IP > direct IP
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"

    def _is_exempt_path(self, path: str) -> bool:
        """
        Checks if the request path is exempt from rate limiting.

        Args:
            path: Request path.

        Returns:
            bool: True if path is exempt, False otherwise.
        """
        exempt_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
        ]
        
        # Exact match for root path
        if path == "/" or path == "":
            return True
            
        # Check if path starts with any exempt path
        return any(path.startswith(exempt_path) for exempt_path in exempt_paths)

    async def dispatch(self, request: Request, call_next):
        """
        Processes each request and applies rate limiting.

        Args:
            request: Incoming request.
            call_next: Next middleware or endpoint.

        Returns:
            Response: HTTP response.
        """
        # Skip rate limiting if disabled or path is exempt
        if not self.enabled:
            return await call_next(request)
            
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        identifier = self._get_client_identifier(request)

        try:
            # Check per-minute limit
            is_allowed, rate_info = self.rate_limiter.check_rate_limit(
                identifier=identifier,
                limit=settings.RATE_LIMIT_PER_MINUTE,
                window=60,
                strategy=settings.RATE_LIMIT_STRATEGY,
            )

            # Add rate limit headers to response
            async def add_rate_limit_headers(response):
                response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
                return response

            if not is_allowed:
                logger.warning(f"Rate limit exceeded for {identifier}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Please try again in {rate_info['retry_after']} seconds.",
                        "limit": rate_info["limit"],
                        "remaining": rate_info["remaining"],
                        "reset": rate_info["reset"],
                        "retry_after": rate_info["retry_after"],
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset"]),
                        "Retry-After": str(rate_info["retry_after"]),
                    },
                )

            response = await call_next(request)
            return await add_rate_limit_headers(response)
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            # On error, allow the request to continue
            return await call_next(request)


def get_redis_client() -> Redis:
    """
    Creates and returns a Redis client instance.

    Returns:
        Redis: Configured Redis client.
    """
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5,
    )
