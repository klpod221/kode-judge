from pydantic_settings import BaseSettings
from pydantic import PostgresDsn
from typing import Optional


class Settings(BaseSettings):
    # Get environment variables for PostgreSQL connection
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432

    # Get environment variables for Redis connection
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PREFIX: str = "kodejudge"

    # Dynamically built database URL
    DATABASE_URL: Optional[PostgresDsn] = None

    # Sandbox execution limits
    SANDBOX_CPU_TIME_LIMIT: float = 2.0
    SANDBOX_CPU_EXTRA_TIME: float = 0.5
    SANDBOX_WALL_TIME_LIMIT: float = 5.0
    SANDBOX_MEMORY_LIMIT: int = 128000
    SANDBOX_MAX_PROCESSES: int = 128
    SANDBOX_MAX_FILE_SIZE: int = 10240
    SANDBOX_NUMBER_OF_RUNS: int = 1

    # Sandbox boolean flags
    SANDBOX_ENABLE_PER_PROCESS_TIME_LIMIT: bool = False
    SANDBOX_ENABLE_PER_PROCESS_MEMORY_LIMIT: bool = False
    SANDBOX_REDIRECT_STDERR_TO_STDOUT: bool = False
    SANDBOX_ENABLE_NETWORK: bool = False

    # Rate limiting configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 20
    RATE_LIMIT_PER_HOUR: int = 100
    RATE_LIMIT_STRATEGY: str = "fixed-window"  # fixed-window or sliding-window

    def __init__(self, **values):
        super().__init__(**values)

        # Build the DATABASE_URL if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )

    class Config:
        # Load environment variables from a .env file if present
        env_file = ".env"


settings = Settings()
