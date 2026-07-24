import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.security import create_access_token
from app.db.models import IntelligenceLeadORM, IntelligenceLeadCaseORM
import uuid
import datetime

def _get_op_by_role(role: str, db: Session):
    op = db.execute(text("SELECT id, district_id FROM operators WHERE role = :role LIMIT 1"), {"role": role}).fetchone()
    if not op:
        pytest.skip(f"No operator found for role {role}")
    return op[0], op[1]

def _create_test_case_in_district(db: Session, district_id: str):
    unit = db.execute(text("SELECT id FROM units WHERE district_id = :did LIMIT 1"), {"did": district_id}).fetchone()
    if not unit:
        pytest.skip(f"No unit found for district {district_id}")
    case_id = str(uuid.uuid4())
    db.execute(text(
        "INSERT INTO cases (id, label, status, updated_at, police_station_id, evidence_count) "
        "VALUES (:id, 'Test Case', 'ACTIVE', 'now', :ps, 0)"
    ), {"id": case_id, "ps": unit[0]})
    return case_id

def _create_test_lead(db: Session, case_ids: list[str], source_cases_json: list = None) -> str:
    lead_id = str(uuid.uuid4())
    lead = IntelligenceLeadORM(
        id=lead_id,
        title="Test Lead",
        priority="HIGH",
        priority_tone="critical",
        source_cases=source_cases_json or []
    )
    db.add(lead)
    db.flush()
    for cid in case_ids:
        db.execute(text("INSERT INTO intelligence_lead_cases (intelligence_lead_id, case_id) VALUES (:lid, :cid)"), {"lid": lead_id, "cid": cid})
    db.commit()
    return lead_id

def test_lead_rbac_command_role(db_session, client):
    op_id, op_district = _get_op_by_role("command", db_session)
    case = db_session.execute(text("SELECT id FROM cases LIMIT 1")).fetchone()
    if not case:
        pytest.skip("No cases found")
        
    lead_id = _create_test_lead(db_session, [case[0]])
    
    token = create_access_token(str(op_id), role="command")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert lead_id in returned_ids

def test_lead_rbac_analyst_same_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    case_id = _create_test_case_in_district(db_session, op_district)
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert lead_id in returned_ids

def test_lead_rbac_analyst_other_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
    case_id = _create_test_case_in_district(db_session, other_dist[0])
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert lead_id not in returned_ids

def test_lead_rbac_field_same_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    case_id = _create_test_case_in_district(db_session, op_district)
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert lead_id in returned_ids

def test_lead_rbac_field_other_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
    case_id = _create_test_case_in_district(db_session, other_dist[0])
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert lead_id not in returned_ids

def test_lead_rbac_multi_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
        
    case_in = _create_test_case_in_district(db_session, op_district)
    case_out = _create_test_case_in_district(db_session, other_dist[0])
    
    # Lead spans two cases: one inside, one outside
    lead_id = _create_test_lead(db_session, [case_in, case_out])
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    # Analyst should see it because ONE case is in their district
    assert lead_id in returned_ids

def test_lead_rbac_orphan_denial(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    lead_id = _create_test_lead(db_session, []) # Orphan
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert lead_id not in returned_ids
    
    op_id_field, _ = _get_op_by_role("field", db_session)
    token_field = create_access_token(str(op_id_field), role="field")
    headers_field = {"Authorization": f"Bearer {token_field}"}
    response_field = client.get("/api/intelligence/leads/mock_session", headers=headers_field)
    returned_ids_field = [s["id"] for s in response_field.json()]
    assert lead_id not in returned_ids_field

def test_lead_rbac_broken_chain(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    
    # Create a case with NO unit (or invalid unit)
    case_id = str(uuid.uuid4())
    db_session.execute(text(
        "INSERT INTO cases (id, label, status, updated_at, police_station_id, evidence_count) "
        "VALUES (:id, 'Test Broken Case', 'ACTIVE', 'now', NULL, 0)"
    ), {"id": case_id})
    db_session.commit()
    
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert lead_id not in returned_ids

def test_lead_rbac_unauthorized_role(db_session, client):
    from app.db.models import OperatorORM
    op_id = "OP-AUDITOR"
    op = OperatorORM(
        id=op_id, operator_id=op_id, name="Auditor", rank="Civilian",
        role="auditor", status="ACTIVE", clearance="Level 1", unit="N/A", assigned_unit="N/A",
        date_of_entry="2026-07-23", biometric_hash="mock_hash"
    )
    db_session.add(op)
    db_session.flush()
    
    token = create_access_token(str(op_id), role="auditor")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 403

def test_lead_rls_ignores_legacy_source_cases(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    
    case_out = _create_test_case_in_district(db_session, other_dist[0])
    
    # Create lead with case OUTSIDE jurisdiction, but legacy source_cases JSON claims a case INSIDE jurisdiction
    case_in = _create_test_case_in_district(db_session, op_district)
    
    # lead_id maps to case_out in the DB relationship, but JSON says case_in
    lead_id = _create_test_lead(db_session, [case_out], source_cases_json=[case_in])
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/intelligence/leads/mock_session", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    # Analyst should NOT see it, because only the formal case_id relationship (case_out) is evaluated
    assert lead_id not in returned_ids
