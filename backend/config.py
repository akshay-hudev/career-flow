from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/careerdb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Gemini
    GEMINI_API_KEY: str = ""

    # Adzuna Job Search API (free tier)
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""

    # App
    SECRET_KEY: str = "change-this-in-production"
    DEBUG: bool = True
    CORS_ORIGINS: list = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://career-platform-delta.vercel.app",
    "https://career-platform-git-main-akshay-hudevs-projects.vercel.app",
    "https://career-platform-akshay-hudevs-projects.vercel.app",
]

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
