from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Manages application settings loaded from environment variables.
    """

    TMDB_API_KEY: str
    DATABASE_URL: str

    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    class Config:
        env_file = ".env"


settings = Settings()
