"""
Test fixtures — uses transactional rollbacks on the PostgreSQL database
to ensure production data is never permanently mutated.
"""
import os
os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.session import Base, get_db
from app.main import app
from app.core.config import settings

# ── Transactional PostgreSQL engine ───────────────────────────────────────────

# We use the existing DATABASE_URL (which should be PostgreSQL)
test_engine = create_engine(settings.DATABASE_URL)
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

