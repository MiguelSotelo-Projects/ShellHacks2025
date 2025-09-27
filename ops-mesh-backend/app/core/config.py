from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ops Mesh - Patient Check-In"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:3001",  # Alternative frontend port
        "https://ops-mesh-frontend.vercel.app",  # Production frontend
    ]

    # Database Settings
    DATABASE_URL: str = "sqlite:///./ops_mesh.db"

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # Google Cloud Settings
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GOOGLE_CLOUD_REGION: str = "us-central1"

    # Google ADK Settings
    ADK_AGENT_ENDPOINT: str = ""
    ADK_API_KEY: str = ""

    # Security Settings
    SECRET_KEY: str = "ops-mesh-hackathon-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Queue Management Settings
    DEFAULT_WAIT_TIME_MINUTES: int = 15
    MAX_QUEUE_SIZE: int = 100
    QUEUE_UPDATE_INTERVAL_SECONDS: int = 30

    # Retry Settings (for Tenacity)
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_SECONDS: int = 2

    # Hospital Settings (Mock Data)
    HOSPITAL_NAME: str = "General Hospital"
    HOSPITAL_ID: str = "GH001"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Validation functions
def validate_google_credentials():
    """Validate Google Cloud credentials are properly configured."""
    if not settings.GOOGLE_CLOUD_PROJECT:
        return False, "GOOGLE_CLOUD_PROJECT not set"

    if not settings.GOOGLE_APPLICATION_CREDENTIALS:
        return False, "GOOGLE_APPLICATION_CREDENTIALS not set"

    if not os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
        return False, "Google credentials file not found"

    return True, "Google credentials configured"


def validate_redis_connection():
    """Validate Redis connection settings."""
    try:
        import redis
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            socket_connect_timeout=5
        )
        r.ping()
        return True, "Redis connection successful"
    except Exception as e:
        return False, f"Redis connection failed: {str(e)}"


def get_database_url():
    """Get the properly formatted database URL."""
    if settings.DATABASE_URL.startswith("sqlite"):
        # Ensure the directory exists for SQLite
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    return settings.DATABASE_URL