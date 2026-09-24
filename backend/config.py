import json
from pydantic_settings import BaseSettings
from functools import lru_cache

# Placeholders that must NEVER be used in production. The startup check below
# fails fast if SECRET_KEY is still one of these while DEBUG is False.
_INSECURE_SECRET_KEYS = {
    "change-this-in-production",
    "change-this-to-a-random-string-in-production",
    "secret",
    "",
}


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/careerdb"

    # Redis
    REDIS_URL: str = ""

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
    # Keep this as a string: pydantic-settings eagerly JSON-decodes list fields,
    # which would reject the convenient comma-separated form before our parser
    # gets a chance to handle it.
    CORS_ORIGINS: str = "*"

    def parse_cors_origins(self) -> list[str]:
        """Read CORS_ORIGINS from a JSON list or comma-separated string."""
        raw = self.CORS_ORIGINS.strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(origin).strip() for origin in parsed if str(origin).strip()]
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()


def assert_production_safe() -> None:
    """Refuse to start in production with an insecure SECRET_KEY or wildcard CORS."""
    if settings.DEBUG:
        return
    if settings.SECRET_KEY in _INSECURE_SECRET_KEYS:
        raise RuntimeError(
            "SECRET_KEY is unset or still the placeholder. "
            "Set a strong SECRET_KEY in the environment before deploying."
        )
    origins = settings.parse_cors_origins()
    if not origins or "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS must be an explicit list of frontend origins in production "
            "(no '*'). Example: CORS_ORIGINS=https://your-app.vercel.app"
        )
