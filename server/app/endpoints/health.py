"""
Health check endpoints for monitoring system status.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.state import get_app_start_time
from app.dependencies.database import get_db
from app.dependencies.queue import get_redis_connection, get_submission_queue
from app.services.health_service import HealthCheckService
from app.schemas.health import (
    HealthResponse,
    DatabaseHealth,
    RedisHealth,
    WorkerHealth,
    SystemInfo,
)

router = APIRouter()


def get_health_service(db: AsyncSession = Depends(get_db)) -> HealthCheckService:
    """
    Provides HealthCheckService instance with dependencies.
    
    Args:
        db: Database session from dependency injection.
        
    Returns:
        HealthCheckService: Service instance.
    """
    redis_conn = get_redis_connection()
    queue = get_submission_queue()
    app_start_time = get_app_start_time()
    return HealthCheckService(db, redis_conn, queue, app_start_time)


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Overall Health Check",
    description="Returns comprehensive health status of all system components including database, Redis, and workers.",
)
async def health_check(
    service: HealthCheckService = Depends(get_health_service),
) -> HealthResponse:
    """
    Performs comprehensive health check of all system components.
    
    Args:
        service: Health check service instance.
        
    Returns:
        HealthResponse: Overall system health status.
    """
    return await service.get_overall_health()


@router.get(
    "/database",
    response_model=DatabaseHealth,
    summary="Database Health Check",
    description="Checks database connectivity and response time.",
)
async def database_health(
    service: HealthCheckService = Depends(get_health_service),
) -> DatabaseHealth:
    """
    Checks database health status.
    
    Args:
        service: Health check service instance.
        
    Returns:
        DatabaseHealth: Database health status.
    """
    return await service.check_database()


@router.get(
    "/redis",
    response_model=RedisHealth,
    summary="Redis Health Check",
    description="Checks Redis connectivity and response time.",
)
async def redis_health(
    service: HealthCheckService = Depends(get_health_service),
) -> RedisHealth:
    """
    Checks Redis health status.
    
    Args:
        service: Health check service instance.
        
    Returns:
        RedisHealth: Redis health status.
    """
    return service.check_redis()


@router.get(
    "/workers",
    response_model=WorkerHealth,
    summary="Workers Health Check",
    description="Returns detailed information about RQ workers including queue size, worker status, and failed jobs.",
)
async def workers_health(
    service: HealthCheckService = Depends(get_health_service),
) -> WorkerHealth:
    """
    Checks worker health and queue status.
    
    Args:
        service: Health check service instance.
        
    Returns:
        WorkerHealth: Worker health status.
    """
    return service.check_workers()


@router.get(
    "/info",
    response_model=SystemInfo,
    summary="System Information",
    description="Returns system information including API version, Python version, uptime, and statistics.",
)
async def system_info(
    service: HealthCheckService = Depends(get_health_service),
) -> SystemInfo:
    """
    Gets system information and statistics.
    
    Args:
        service: Health check service instance.
        
    Returns:
        SystemInfo: System information.
    """
    return await service.get_system_info()


@router.get(
    "/ping",
    summary="Simple Ping",
    description="Simple ping endpoint for basic availability check.",
)
async def ping():
    """
    Simple ping endpoint.
    
    Returns:
        dict: Pong response.
    """
    return {"status": "ok", "message": "pong"}
