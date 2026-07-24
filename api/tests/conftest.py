"""
Test fixtures — uses transactional rollbacks on the PostgreSQL database
to ensure production data is never permanently mutated.

NOTE: This file itself imports nothing that was deleted in the
legacy-DB/auth/AI cleanup pass, so it still collects and its `client`/
`db_session` fixtures still construct. However `auth_token` (and anything
depending on it, e.g. `headers`) POSTs to /api/auth/login, which now
returns 501 since the legacy JWT auth implementation was removed ahead of
Catalyst Authentication (LUMEN_MASTER_SPEC_V3 Session 3) — that fixture
will fail at runtime with an assertion error, not at collection time.
`db_session`/`setup_test_db` also assume a live PostgreSQL connection,
which is no longer required for the app to boot but is still required
for any test that uses these fixtures.
"""
import os
# Mark the process as a test run before settings load, so APP_ENV/TESTING are
# consistent. Configuration itself comes from the single root .env via
# lumen.config — no test-specific env loading here.
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from lumen.db.session import Base, get_db
from main import app
from lumen.config import settings

# ── Transactional PostgreSQL engine ───────────────────────────────────────────

# The Postgres-backed fixtures use TEST_DATABASE_URL when it is explicitly set,
# otherwise DATABASE_URL — resolved centrally in lumen.config (no hidden
# default). create_engine is lazy, so importing this module does not require a
# live DB; the in-memory SQLite unit tests never touch this engine.
test_engine = create_engine(settings.test_database_url)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def setup_test_db():
    # Do NOT drop or recreate tables, just ensure we can connect.
    pass

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session wrapped in a transaction."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """TestClient with the DB dependency overridden to the transactional session."""
    def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_token(client):
    """Return a valid JWT obtained via the login endpoint."""
    resp = client.post(
        "/api/auth/login",
        json={"clearance_id": "OP-7729", "passphrase": "password"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture(scope="function")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

