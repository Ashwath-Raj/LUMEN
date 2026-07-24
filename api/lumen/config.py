"""
Core application settings loaded from environment variables.
Uses python-dotenv / os.environ with sane defaults for development.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()


def _normalise_db_url(url: str) -> str:
    """
    Ensure the URL uses the psycopg3 SQLAlchemy dialect.
    Converts  postgresql://...  →  postgresql+psycopg://...
    Leaves    postgresql+psycopg://...  unchanged.
    """
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1).replace(
            "postgres://", "postgresql+psycopg://", 1
        )
    return url


class Settings:
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "LUMEN Crime Intelligence Platform")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"
    
    # Dataset Generation Settings
    SEED_RANDOM: int = int(os.getenv("SEED_RANDOM", "42"))
    DATASET_SCALE: str = os.getenv("DATASET_SCALE", "small").lower()

    # CORS — the Vite dev server runs on 5173/5174
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
    ).split(",")

    # Database — psycopg3 dialect required (postgresql+psycopg://)
    DATABASE_URL: str = _normalise_db_url(
        os.getenv("DATABASE_URL", "postgresql+psycopg://lumen:lumen@localhost:5432/lumen")
    )

    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # graph/legacy_neo4j_service.py (kept per ADR-001 as reference material)
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_ENABLED: bool = os.getenv("NEO4J_ENABLED", "false").lower() == "true"

    # API Prefix / Version
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    API_VERSION: str = os.getenv("API_VERSION", "v1")


settings = Settings()

