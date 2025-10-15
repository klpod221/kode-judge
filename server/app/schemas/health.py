"""
Health check schemas for API responses.
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class DatabaseHealth(BaseModel):
    """Database health status."""
    
    status: str
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


class RedisHealth(BaseModel):
    """Redis health status."""
    
    status: str
    response_time_ms: Optional[float] = None
    ping: Optional[str] = None
    error: Optional[str] = None


class WorkerHealth(BaseModel):
    """Worker health status."""
    
    queue_name: str
    queue_size: int
    workers_total: int
    workers_busy: int
    workers_idle: int
    failed_jobs: int
    status: str


class HealthResponse(BaseModel):
    """Overall health check response."""
    
    status: str
    timestamp: datetime
    version: str
    database: DatabaseHealth
    redis: RedisHealth
    workers: WorkerHealth


class SystemInfo(BaseModel):
    """System information response."""
    
    api_version: str
    python_version: str
    environment: str
    uptime_seconds: Optional[float] = None
    supported_languages_count: int
    total_submissions: int
