"""
Centralized application configuration — the single source of settings for the
LUMEN backend.

Design (production-grade config architecture):
  * ONE canonical env file at the repository root (`LUMEN/.env`). This module
    resolves that path explicitly, so configuration does not depend on the
    process's current working directory (uvicorn from `api/`, pytest from the
    repo root, and Docker all read the same file).
  * Built on Pydantic Settings (`pydantic-settings`): types are validated,
    and precedence is the standard, explicit order — real environment
    variables override the root `.env`, which overrides the in-code defaults.
  * NO invented credentials. `DATABASE_URL` is REQUIRED and has no default; if
    it is missing the app fails fast at startup with a clear error rather than
    silently connecting to a production-looking `lumen:lumen@localhost` URL.
  * Only variables the codebase actually reads are defined here. Auth/JWT and
    AI-provider settings are intentionally absent: those subsystems were
    removed ahead of the LUMEN_MASTER_SPEC_V3 rebuild (Catalyst Authentication,
    Session 3; AI orchestrator, Session 14) and are not read anywhere today.
    Adding them now would be config the project does not use.

This is the ONLY settings class and the ONLY place `.env` is loaded.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The one canonical env file: repository root, two levels up from this file
# (api/lumen/config.py -> api/ -> LUMEN/).
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


def _normalise_db_url(url: str) -> str:
    """Ensure the URL uses the psycopg3 SQLAlchemy dialect.
    `postgresql://...` / `postgres://...` → `postgresql+psycopg://...`;
    an already-qualified `postgresql+psycopg://...` is left unchanged."""
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ROOT_ENV,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",          # root .env also carries VITE_* (frontend-only); ignore them here
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "LUMEN Crime Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"          # development | production | test
    DEBUG: bool = False
    TESTING: bool = False

    # ── Dataset / seed ───────────────────────────────────────────────────
    SEED_RANDOM: int = 42
    DATASET_SCALE: str = "small"

    # ── Database (REQUIRED — no default; fail fast if missing) ───────────
    # psycopg3 dialect enforced by the validator below.
    DATABASE_URL: str = Field(..., min_length=1)
    # Optional override for the test database; falls back to DATABASE_URL when
    # unset (see `test_database_url`). No hidden default.
    TEST_DATABASE_URL: str | None = None

    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # ── CORS ─────────────────────────────────────────────────────────────
    # Stored as a raw comma-separated string (pydantic-settings would try to
    # JSON-decode a `list[str]` env value, which a plain comma list is not).
    # The parsed list is exposed via the `cors_origins` property below.
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )

    # ── API routing ──────────────────────────────────────────────────────
    API_PREFIX: str = "/api"
    API_VERSION: str = "v1"

    # ── Neo4j (legacy reference service, ADR-001; only read when enabled) ─
    # Non-secret local defaults used solely by the optional, disabled-by-
    # default legacy graph service; the real graph runs in-process (ADR-001).
    # NEO4J_ENABLED is false unless explicitly turned on.
    NEO4J_ENABLED: bool = False
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""

    # ─────────────────────────────────────────────────────────────────────

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def _dialect(cls, v: str) -> str:
        return _normalise_db_url(v)

    @field_validator("TEST_DATABASE_URL", mode="after")
    @classmethod
    def _test_dialect(cls, v: str | None) -> str | None:
        return _normalise_db_url(v) if v else v

    @property
    def cors_origins(self) -> list[str]:
        """The allowed CORS origins as a clean list, parsed from the
        comma-separated `CORS_ORIGINS` env value."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def test_database_url(self) -> str:
        """The database tests should use: `TEST_DATABASE_URL` when explicitly
        provided, otherwise `DATABASE_URL`. No hidden fallback beyond that."""
        return self.TEST_DATABASE_URL or self.DATABASE_URL


def _load_settings() -> "Settings":
    """Instantiate settings, converting Pydantic's validation error for a
    missing/blank DATABASE_URL into a clear, actionable startup message —
    fail fast, never invent credentials."""
    try:
        return Settings()
    except Exception as exc:  # pydantic ValidationError (or env parse error)
        raise RuntimeError(
            "LUMEN configuration error: a required environment variable is "
            "missing or invalid.\n"
            f"Expected the canonical env file at: {_ROOT_ENV}\n"
            "At minimum, DATABASE_URL must be set (e.g. "
            "postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME).\n"
            "Copy .env.example to .env at the repository root and fill it in.\n"
            f"\nUnderlying error: {exc}"
        ) from exc


settings = _load_settings()
