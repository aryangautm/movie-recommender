from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """
    Manages application settings loaded from environment variables.
    """

    CORS_ORIGINS: str

    TMDB_API_KEY: str
    TMDB_API_V4_ACCESS_TOKEN: str
    DATABASE_URL: str

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    REDIS_URL: str

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
