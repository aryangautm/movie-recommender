from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Manages application settings loaded from environment variables.
    """

    TMDB_API_KEY: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
