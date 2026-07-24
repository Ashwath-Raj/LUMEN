"""
Database session management.

- Uses `create_engine` with connection pooling tuned for the app.
- `get_db()` is a FastAPI dependency that provides a scoped session per request.
- `engine` and `Base` are module-level singletons imported by Alembic's env.py.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from lumen.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,          # reconnect if a pooled connection drops
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,      # objects remain accessible after commit
)

from sqlalchemy import MetaData
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)


def get_db():
    """
    FastAPI dependency — yields a DB session, guarantees close on teardown.
    Usage:
        @router.get("/...")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """Health-check helper — returns True if the DB is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
