"""
Schema definitions for rate limiting responses.
"""

from pydantic import BaseModel, Field
from typing import Optional


class RateLimitError(BaseModel):
    """
    Response schema for rate limit exceeded errors.
    """

    error: str = Field(
        ...,
        description="Error type identifier",
        example="Rate limit exceeded",
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        example="Too many requests. Please try again in 30 seconds.",
    )
    limit: int = Field(
        ...,
        description="Maximum number of requests allowed in the time window",
        example=20,
    )
    remaining: int = Field(
        ...,
        description="Number of requests remaining in the current window",
        example=0,
    )
    reset: int = Field(
        ...,
        description="Unix timestamp when the rate limit resets",
        example=1697456789,
    )
    retry_after: Optional[int] = Field(
        None,
        description="Number of seconds to wait before retrying",
        example=30,
    )


class RateLimitInfo(BaseModel):
    """
    Rate limit information included in response headers.
    """

    limit: int = Field(
        ...,
        description="Maximum requests allowed per window",
        example=20,
    )
    remaining: int = Field(
        ...,
        description="Remaining requests in current window",
        example=15,
    )
    reset: int = Field(
        ...,
        description="Unix timestamp when the limit resets",
        example=1697456789,
    )
