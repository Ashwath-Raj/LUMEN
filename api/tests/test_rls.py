"""
NOTE: Tests the deleted legacy JWT auth (lumen.identity.security).
Expected to fail import/collection until Catalyst Authentication is
rebuilt in a later LUMEN_MASTER_SPEC_V3 session (Session 3). Left as-is
(not deleted, not patched) per the sanitation-pass scope.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
from main import app
from lumen.db.session import SessionLocal
from lumen.identity.security import create_access_token

client = TestClient(app)

def test_rls_filtering():
    with SessionLocal() as db:
        op = db.execute(text("SELECT id, role, district_id FROM operators WHERE role = 'analyst' LIMIT 1")).fetchone()
        if not op:
            pytest.skip("No analyst found to test RLS")
            
        op_id, role, op_district = op
        
        district_cases = db.execute(text(
            "SELECT c.id FROM cases c "
            "JOIN units u ON c.police_station_id = u.id "
            "WHERE u.district_id = :d"
        ), {"d": op_district}).fetchall()
        
        expected_case_ids = {c[0] for c in district_cases}
        
    token = create_access_token(str(op_id), role=str(role))
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/investigation/cases", headers=headers)
    assert response.status_code == 200
    
    returned_cases = response.json()
    returned_case_ids = {c["id"] for c in returned_cases}
    
    assert returned_case_ids == expected_case_ids

