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

# The legacy ORM models (lumen.db.models.legacy_models) were deleted as part
# of the cleanup ahead of LUMEN_MASTER_SPEC_V3's canonical DB schema rebuild
# (Session 2). There is currently no models module to source metadata from,
# so autogenerate support is disabled until Session 2 reintroduces a
# canonical models module and this is pointed at its Base.metadata.
target_metadata = None


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
