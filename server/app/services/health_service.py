"""
Health check service for monitoring system components.
"""
import time
import sys
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis import Redis
from rq import Queue
from rq.worker import Worker

from app.db.models import Language, Submission
from app.schemas.health import (
    HealthResponse,
    DatabaseHealth,
    RedisHealth,
    WorkerHealth,
    SystemInfo,
)


class HealthCheckService:
    """Service for performing health checks on system components."""
    
    def __init__(self, db: AsyncSession, redis_conn: Redis, queue: Queue, app_start_time: float):
        """
        Initializes health check service.
        
        Args:
            db: Database session.
            redis_conn: Redis connection.
            queue: Job queue.
            app_start_time: Application start timestamp.
        """
        self.db = db
        self.redis_conn = redis_conn
        self.queue = queue
        self.app_start_time = app_start_time
    
    async def check_database(self) -> DatabaseHealth:
        """
        Checks database connectivity and response time.
        
        Returns:
            DatabaseHealth: Database health status.
        """
        try:
            start = time.time()
            await self.db.execute(text("SELECT 1"))
            response_time = (time.time() - start) * 1000
            
            return DatabaseHealth(
                status="healthy",
                response_time_ms=round(response_time, 2),
            )
        except Exception as e:
            return DatabaseHealth(
                status="unhealthy",
                error=str(e),
            )
    
    def check_redis(self) -> RedisHealth:
        """
        Checks Redis connectivity and response time.
        
        Returns:
            RedisHealth: Redis health status.
        """
        try:
            start = time.time()
            ping_result = self.redis_conn.ping()
            response_time = (time.time() - start) * 1000
            
            return RedisHealth(
                status="healthy",
                response_time_ms=round(response_time, 2),
                ping="pong" if ping_result else "failed",
            )
        except Exception as e:
            return RedisHealth(
                status="unhealthy",
                error=str(e),
            )
    
    def check_workers(self) -> WorkerHealth:
        """
        Checks worker status and queue information.
        
        Returns:
            WorkerHealth: Worker health status.
        """
        try:
            workers = Worker.all(connection=self.redis_conn)
            queue_size = len(self.queue)
            failed_count = self.queue.failed_job_registry.count
            
            workers_busy = sum(1 for w in workers if w.get_state() == "busy")
            workers_idle = len(workers) - workers_busy
            
            status = "healthy"
            if len(workers) == 0:
                status = "no_workers"
            elif queue_size > 100:
                status = "high_load"
            elif failed_count > 10:
                status = "degraded"
            
            return WorkerHealth(
                queue_name=self.queue.name,
                queue_size=queue_size,
                workers_total=len(workers),
                workers_busy=workers_busy,
                workers_idle=workers_idle,
                failed_jobs=failed_count,
                status=status,
            )
        except Exception as e:
            return WorkerHealth(
                queue_name=self.queue.name,
                queue_size=0,
                workers_total=0,
                workers_busy=0,
                workers_idle=0,
                failed_jobs=0,
                status=f"error: {str(e)}",
            )
    
    async def get_overall_health(self) -> HealthResponse:
        """
        Performs comprehensive health check.
        
        Returns:
            HealthResponse: Overall system health.
        """
        db_health = await self.check_database()
        redis_health = self.check_redis()
        worker_health = self.check_workers()
        
        overall_status = "healthy"
        if (
            db_health.status != "healthy"
            or redis_health.status != "healthy"
            or worker_health.status in ["no_workers", "error"]
        ):
            overall_status = "unhealthy"
        elif worker_health.status in ["high_load", "degraded"]:
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            database=db_health,
            redis=redis_health,
            workers=worker_health,
        )
    
    async def get_system_info(self) -> SystemInfo:
        """
        Gets system information and statistics.
        
        Returns:
            SystemInfo: System information.
        """
        lang_count_result = await self.db.execute(select(Language))
        languages_count = len(lang_count_result.scalars().all())
        
        submission_count_result = await self.db.execute(select(Submission))
        submissions_count = len(submission_count_result.scalars().all())
        
        uptime = time.time() - self.app_start_time
        
        return SystemInfo(
            api_version="1.0.0",
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            environment="production",
            uptime_seconds=round(uptime, 2),
            supported_languages_count=languages_count,
            total_submissions=submissions_count,
        )
