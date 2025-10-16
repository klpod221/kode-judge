"""
Worker manager utility for cleaning up stale workers.
"""
import redis
import logging
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)


class WorkerManager:
    """Manages RQ worker lifecycle and cleanup."""
    
    def __init__(self, redis_url: str = None):
        """
        Initializes worker manager.
        
        Args:
            redis_url: Redis connection URL. If None, builds from settings.
        """
        if redis_url is None:
            redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        
        self.redis_client = redis.from_url(redis_url)
        self.queue_prefix = settings.REDIS_PREFIX
    
    def get_all_workers(self) -> List[str]:
        """
        Gets all registered workers in Redis.
        
        Returns:
            List[str]: List of worker names.
        """
        worker_keys = self.redis_client.keys("rq:worker:*")
        workers = []
        
        for key in worker_keys:
            key_str = key.decode("utf-8")
            if ":birth" not in key_str and ":death" not in key_str:
                worker_name = key_str.replace("rq:worker:", "")
                workers.append(worker_name)
        
        return workers
    
    def is_worker_active(self, worker_name: str) -> bool:
        """
        Checks if a worker is actually active.
        
        Args:
            worker_name: Name of the worker.
            
        Returns:
            bool: True if worker is active.
        """
        worker_key = f"rq:worker:{worker_name}"
        
        if not self.redis_client.exists(worker_key):
            return False
        
        return self.redis_client.sismember("rq:workers", worker_key)
    
    def cleanup_worker(self, worker_name: str) -> bool:
        """
        Cleans up a single worker registration.
        
        Args:
            worker_name: Name of the worker to cleanup.
            
        Returns:
            bool: True if cleanup was successful.
        """
        try:
            worker_key = f"rq:worker:{worker_name}"
            
            self.redis_client.delete(worker_key)
            self.redis_client.delete(f"{worker_key}:birth")
            self.redis_client.delete(f"{worker_key}:death")
            self.redis_client.srem("rq:workers", worker_name)
            
            logger.info(f"Cleaned up worker: {worker_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup worker {worker_name}: {e}")
            return False
    
    def cleanup_all_workers(self) -> int:
        """
        Cleans up all registered workers.
        
        Returns:
            int: Number of workers cleaned up.
        """
        workers = self.get_all_workers()
        cleaned = 0
        
        for worker in workers:
            if self.cleanup_worker(worker):
                cleaned += 1
        
        return cleaned
    
    def cleanup_stale_workers(self) -> int:
        """
        Cleans up only stale (inactive) workers.
        
        Returns:
            int: Number of stale workers cleaned up.
        """
        workers = self.get_all_workers()
        cleaned = 0
        
        for worker in workers:
            if not self.is_worker_active(worker):
                if self.cleanup_worker(worker):
                    cleaned += 1
        
        return cleaned
    
    def get_worker_info(self, worker_name: str) -> dict:
        """
        Gets information about a specific worker.
        
        Args:
            worker_name: Name of the worker.
            
        Returns:
            dict: Worker information.
        """
        worker_key = f"rq:worker:{worker_name}"
        
        if not self.redis_client.exists(worker_key):
            return {"exists": False}
        
        worker_data = self.redis_client.hgetall(worker_key)
        birth = self.redis_client.get(f"{worker_key}:birth")
        death = self.redis_client.get(f"{worker_key}:death")
        
        return {
            "exists": True,
            "name": worker_name,
            "data": {k.decode(): v.decode() for k, v in worker_data.items()},
            "birth": birth.decode() if birth else None,
            "death": death.decode() if death else None,
            "is_active": self.is_worker_active(worker_name),
        }
    
    def list_all_workers_info(self) -> List[dict]:
        """
        Lists information about all workers.
        
        Returns:
            List[dict]: List of worker information dictionaries.
        """
        workers = self.get_all_workers()
        return [self.get_worker_info(worker) for worker in workers]


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    manager = WorkerManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            workers = manager.list_all_workers_info()
            if workers:
                print(f"Found {len(workers)} worker(s):")
                for w in workers:
                    status = "ACTIVE" if w.get("is_active") else "STALE"
                    print(f"  - {w['name']} ({status})")
            else:
                print("No workers found")
        
        elif command == "cleanup":
            cleaned = manager.cleanup_all_workers()
            print(f"Cleaned up {cleaned} worker(s)")
        
        elif command == "cleanup-stale":
            cleaned = manager.cleanup_stale_workers()
            print(f"Cleaned up {cleaned} stale worker(s)")
        
        elif command == "info" and len(sys.argv) > 2:
            worker_name = sys.argv[2]
            info = manager.get_worker_info(worker_name)
            if info["exists"]:
                print(f"Worker: {worker_name}")
                print(f"  Active: {info['is_active']}")
                print(f"  Birth: {info['birth']}")
                print(f"  Death: {info['death']}")
                print(f"  Data: {info['data']}")
            else:
                print(f"Worker '{worker_name}' not found")
        
        else:
            print("Unknown command")
            sys.exit(1)
    else:
        print("Usage:")
        print("  python -m app.worker_manager list")
        print("  python -m app.worker_manager cleanup")
        print("  python -m app.worker_manager cleanup-stale")
        print("  python -m app.worker_manager info <worker_name>")
