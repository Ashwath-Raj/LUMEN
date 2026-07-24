"""
Alembic environment — wired to LUMEN settings and ORM metadata.
"""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from lumen.config import settings

config = context.config

# Override sqlalchemy.url from settings (respects DATABASE_URL env var)
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("%", "%%")
)

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass

# Point autogenerate/migrations at the canonical ORM metadata. Importing these
# model modules registers every table on `Base.metadata`:
#   * canonical.py — the 27 official KSP tables + inv_arrestsurrenderaccused (§3.5/§3.4)
#   * identity.py  — lumen_person / lumen_person_link / lumen_person_dispute (§3.6, §6)
#   * quality.py   — lumen_quality_finding / lumen_quality_score (§3.6, §5)
# Import for side effects (table registration); the modules need not be named.
from lumen.db.session import Base  # noqa: E402
from lumen.db.models import canonical as _canonical  # noqa: E402,F401
from lumen.db.models import identity as _identity     # noqa: E402,F401
from lumen.db.models import quality as _quality        # noqa: E402,F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live connection needed)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            compare_type=True,         # detect column type changes
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
