"""
Database bootstrap — LUMEN.

Brings a fresh PostgreSQL instance to a fully-migrated LUMEN schema WITHOUT
starting the FastAPI backend. After this runs, every table is inspectable in
DBeaver / psql immediately.

Steps (each reported, fail-fast on error):
  1. Verify PostgreSQL connectivity (connect to the server's maintenance DB).
  2. Create the target database if it does not exist.
  3. Run `alembic upgrade head` (the single canonical baseline builds the schema).
  4. Verify every expected table exists; exit non-zero if any are missing.

Configuration comes solely from the centralized settings (root .env /
DATABASE_URL) — no credentials are hardcoded here. The app never calls
Base.metadata.create_all(); this script (via Alembic) is the only path that
creates schema.

Usage (from the api/ directory, inside the venv):
    python -m scripts.init_db
or:
    python scripts/init_db.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a bare script (`python scripts/init_db.py`) as well as a
# module (`python -m scripts.init_db`) by ensuring api/ is importable.
_API_DIR = Path(__file__).resolve().parents[1]
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

import psycopg
from psycopg import sql
from sqlalchemy import inspect
from sqlalchemy.engine.url import make_url

from lumen.config import settings
from lumen.db.session import Base, engine

# Import model modules so Base.metadata carries the full table set for the
# post-migration verification (§3.5 canonical + §3.6 lumen_).
from lumen.db.models import canonical as _canonical  # noqa: F401
from lumen.db.models import identity as _identity     # noqa: F401
from lumen.db.models import quality as _quality        # noqa: F401
from lumen.db.models import intelligence as _intel     # noqa: F401
from lumen.db.models import graph as _graph            # noqa: F401
from lumen.db.models import prediction as _prediction  # noqa: F401
from lumen.db.models import event as _event            # noqa: F401
from lumen.db.models import kb as _kb                  # noqa: F401
from lumen.db.models import prompt as _prompt          # noqa: F401
from lumen.db.models import eval as _eval              # noqa: F401
from lumen.db.models import policy as _policy          # noqa: F401
from lumen.db.models import registry as _registry      # noqa: F401
from lumen.db.models import feature as _feature        # noqa: F401


# ── small console helpers ──────────────────────────────────────────────────
def _ok(msg: str) -> None:
    print(f"  [ok]   {msg}")


def _info(msg: str) -> None:
    print(f"  [info] {msg}")


def _fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"  [FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


def _step(n: int, title: str) -> None:
    print(f"\n[{n}/4] {title}")


def _psycopg_dsn(url) -> str:
    """A libpq DSN (psycopg) from a SQLAlchemy URL, dropping the +psycopg
    driver suffix that libpq does not understand."""
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def main() -> None:
    print("LUMEN database bootstrap")
    url = make_url(settings.DATABASE_URL)
    target_db = url.database
    if not target_db:
        _fail("DATABASE_URL has no database name.")
    print(f"  target: {url.host}:{url.port or 5432}/{target_db} (user: {url.username})")

    # ── 1. connectivity ────────────────────────────────────────────────
    _step(1, "Verify PostgreSQL connectivity")
    # Connect to the 'postgres' maintenance DB so we can create the target if
    # it does not exist yet.
    maint_url = url.set(database="postgres")
    try:
        with psycopg.connect(_psycopg_dsn(maint_url), connect_timeout=10) as conn:
            conn.execute("SELECT 1")
        _ok(f"connected to server at {url.host}:{url.port or 5432}")
    except Exception as exc:  # noqa: BLE001
        _fail(
            "cannot connect to PostgreSQL.\n"
            f"         {exc}\n"
            "         Check the server is running and DATABASE_URL credentials are correct."
        )

    # ── 2. create database if absent ───────────────────────────────────
    _step(2, "Create target database if it does not exist")
    try:
        with psycopg.connect(_psycopg_dsn(maint_url), autocommit=True, connect_timeout=10) as conn:
            exists = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (target_db,)
            ).fetchone()
            if exists:
                _info(f"database '{target_db}' already exists")
            else:
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
                _ok(f"created database '{target_db}'")
    except Exception as exc:  # noqa: BLE001
        _fail(f"could not create database '{target_db}': {exc}")

    # ── 3. alembic upgrade head ────────────────────────────────────────
    _step(3, "Run Alembic migrations (upgrade head)")
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(str(_API_DIR / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(_API_DIR / "alembic"))
        # env.py reads settings.DATABASE_URL itself; nothing else to wire.
        command.upgrade(alembic_cfg, "head")
        _ok("alembic upgrade head complete")
    except Exception as exc:  # noqa: BLE001
        _fail(f"alembic upgrade failed: {exc}")

    # ── 4. verify expected tables ──────────────────────────────────────
    _step(4, "Verify expected tables exist")
    expected = set(Base.metadata.tables.keys())
    inspector = inspect(engine)
    present = set(inspector.get_table_names())
    missing = sorted(expected - present)
    if missing:
        _fail(
            f"{len(missing)} expected table(s) missing after migration: "
            + ", ".join(missing)
        )
    _ok(f"all {len(expected)} expected tables present")
    # 'alembic_version' is created by Alembic itself (not in ORM metadata).
    extra_platform = sorted(t for t in present if t == "alembic_version")
    print("\nTables now in the database "
          f"({len(present)} total, {len(expected)} LUMEN + {len(extra_platform)} alembic):")
    for name in sorted(present):
        marker = " " if name in expected else "*"
        print(f"  {marker} {name}")

    print("\nDone. The schema is fully migrated and inspectable in DBeaver/psql "
          "without starting the backend.")


if __name__ == "__main__":
    main()
