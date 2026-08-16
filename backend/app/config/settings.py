"""
Centralised application configuration.

Everything here is sourced from environment variables (see .env.example).
Nothing that belongs in .env is ever hardcoded - see project rule
"never hardcode secrets".
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    APP_NAME: str = "Smart Department Timetable Management System"
    ENVIRONMENT: str = "development"  # development | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- MongoDB ---
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "smart_timetable_db"

    # --- JWT / Auth ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME: int = 30
    REFRESH_COOKIE_NAME: str = "refresh_token"
    MAX_ACTIVE_SESSIONS_PER_USER: int = 5

    # --- CORS ---
    # Comma-separated origins in .env, e.g. "http://localhost:5173,https://timetable.example.edu"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:80,http://localhost"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # --- Initial Super Admin bootstrap ---
    # On first startup, if no users exist yet, one Super Admin account is
    # created automatically from these values so there is always a way
    # to log in. Change the password immediately after first login.
    SUPER_ADMIN_NAME: str = "System Administrator"
    SUPER_ADMIN_EMAIL: str = "admin@college.edu"
    SUPER_ADMIN_PASSWORD: str = "Admin@123456"

    # --- Rate limiting ---
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "120/minute"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached so Settings() (which reads the environment/.env) only runs once."""
    return Settings()
