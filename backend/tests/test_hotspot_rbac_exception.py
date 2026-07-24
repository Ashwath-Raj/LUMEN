import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_hotspot_rbac_exception_command(client, headers):
    """Verify Command role can access Hotspots globally."""
    # The default 'headers' fixture is for OP-7729, which is a command role.
    response = client.get("/api/geospatial/hotspots", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.fixture
def analyst_headers(client, db_session):
    from app.db.models import OperatorORM
    analyst = db_session.query(OperatorORM).filter(OperatorORM.role == "analyst").first()
    resp = client.post("/api/auth/login", json={"clearance_id": analyst.id, "passphrase": "password"})
    return {"Authorization": f"Bearer {resp.json()['token']}"}

@pytest.fixture
def field_headers(client, db_session):
    from app.db.models import OperatorORM
    field_op = db_session.query(OperatorORM).filter(OperatorORM.role == "field").first()
    resp = client.post("/api/auth/login", json={"clearance_id": field_op.id, "passphrase": "password"})
    return {"Authorization": f"Bearer {resp.json()['token']}"}

def test_hotspot_rbac_exception_analyst(client, analyst_headers):
    """
    Verify Analyst role can access Hotspots globally.
    This is an explicitly approved TEMPORARY RBAC EXCEPTION.
    Jurisdictional RLS is not applied because Hotspots lack a deterministic ownership model.
    """
    response = client.get("/api/geospatial/hotspots", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Analyst should see all Hotspots under the temporary exception"

def test_hotspot_rbac_exception_field(client, field_headers):
    """
    Verify Field role can access Hotspots globally.
    This is an explicitly approved TEMPORARY RBAC EXCEPTION.
    """
    response = client.get("/api/geospatial/hotspots", headers=field_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0, "Field should see all Hotspots under the temporary exception"

@pytest.fixture
def mock_htt_headers():
    import app.dependencies.auth as auth
    from app.models.operator import Operator
    
    def _mock_op():
        return Operator(
            id="htt-mock",
            name="HTT Mock",
            rank="Officer",
            role="htt",
            clearance="SECRET",
            unit="HQ",
            date_of_entry="2023-01-01",
            biometric_hash="hash",
            operator_id="OP-HTT",
            status="ACTIVE"
        )
    
    app.dependency_overrides[auth.get_current_operator] = _mock_op
    yield {"Authorization": "Bearer mock-token"}
    app.dependency_overrides = {}

def test_hotspot_rbac_unauthorized_role_enforced(client, mock_htt_headers):
    """Verify unauthorized roles receive 403 Forbidden."""
    response = client.get("/api/geospatial/hotspots", headers=mock_htt_headers)
    assert response.status_code == 403
    assert "Insufficient clearance" in response.json()["detail"]
