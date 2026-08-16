from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/careerdb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Gemini
    GEMINI_API_KEY: str = ""
    # Model is configurable so a retired model can be swapped without a code change.
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Adzuna Job Search API (free tier)
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""

    # App
    SECRET_KEY: str = "change-this-in-production"
    DEBUG: bool = True
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
