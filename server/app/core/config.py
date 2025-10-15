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
