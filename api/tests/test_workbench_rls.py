"""
NOTE: Tests the deleted legacy JWT auth (lumen.identity.security) and the
deleted legacy DB models (lumen.db.models.legacy_models). Expected to fail
import/collection until these subsystems are rebuilt in later
LUMEN_MASTER_SPEC_V3 sessions (Session 2 for the canonical DB schema,
Session 3 for Catalyst Authentication). Left as-is (not deleted, not
patched) per the sanitation-pass scope.
"""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from lumen.identity.security import create_access_token
from lumen.db.models.legacy_models import IntelligenceLeadORM, IntelligenceLeadCaseORM
import uuid

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

def get_workbench_lead_ids(client, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/intelligence/workbench", headers=headers)
    if response.status_code != 200:
        return response.status_code, None
    data = response.json()
    return 200, [lead["id"] for lead in data.get("generatedLeads", [])]

def test_workbench_rbac_command_role(db_session, client):
    op_id, op_district = _get_op_by_role("command", db_session)
    case = db_session.execute(text("SELECT id FROM cases LIMIT 1")).fetchone()
    if not case:
        pytest.skip("No cases found")
    
    lead_id = _create_test_lead(db_session, [case[0]])
    token = create_access_token(str(op_id), role="command")
    
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    assert lead_id in returned_ids

def test_workbench_rbac_analyst_same_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    case_id = _create_test_case_in_district(db_session, op_district)
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="analyst")
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    assert lead_id in returned_ids

def test_workbench_rbac_analyst_other_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
    case_id = _create_test_case_in_district(db_session, other_dist[0])
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="analyst")
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    assert lead_id not in returned_ids

def test_workbench_rbac_field_same_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    case_id = _create_test_case_in_district(db_session, op_district)
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="field")
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    assert lead_id in returned_ids

def test_workbench_rbac_field_other_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
    case_id = _create_test_case_in_district(db_session, other_dist[0])
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="field")
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    assert lead_id not in returned_ids

def test_workbench_rbac_multi_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
        
    case_in = _create_test_case_in_district(db_session, op_district)
    case_out = _create_test_case_in_district(db_session, other_dist[0])
    
    lead_id = _create_test_lead(db_session, [case_in, case_out])
    
    token = create_access_token(str(op_id), role="analyst")
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    assert lead_id in returned_ids

def test_workbench_rbac_orphan_denial(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    lead_id = _create_test_lead(db_session, []) # Orphan
    
    token = create_access_token(str(op_id), role="analyst")
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    assert lead_id not in returned_ids
    
    op_id_field, _ = _get_op_by_role("field", db_session)
    token_field = create_access_token(str(op_id_field), role="field")
    status_field, returned_ids_field = get_workbench_lead_ids(client, token_field)
    assert status_field == 200
    assert lead_id not in returned_ids_field

def test_workbench_rbac_broken_chain(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    case_id = str(uuid.uuid4())
    db_session.execute(text(
        "INSERT INTO cases (id, label, status, updated_at, police_station_id, evidence_count) "
        "VALUES (:id, 'Test Case', 'ACTIVE', 'now', NULL, 0)"
    ), {"id": case_id})
    
    lead_id = _create_test_lead(db_session, [case_id])
    
    token = create_access_token(str(op_id), role="analyst")
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    assert lead_id not in returned_ids

def test_workbench_rbac_unauthorized_role(db_session, client):
    op_id, _ = _get_op_by_role("partner_agency", db_session)
    token = create_access_token(str(op_id), role="partner_agency")
    status, _ = get_workbench_lead_ids(client, token)
    assert status == 403

def test_workbench_rls_ignores_legacy_source_cases(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    case_id = _create_test_case_in_district(db_session, op_district)
    
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
    other_case_id = _create_test_case_in_district(db_session, other_dist[0])
    
    # 1. Lead with right jurisdiction in JSON, wrong jurisdiction formally -> Denied
    lead_id_1 = _create_test_lead(db_session, [other_case_id], source_cases_json=[case_id])
    
    # 2. Lead with wrong jurisdiction in JSON, right jurisdiction formally -> Allowed
    lead_id_2 = _create_test_lead(db_session, [case_id], source_cases_json=[other_case_id])
    
    token = create_access_token(str(op_id), role="analyst")
    status, returned_ids = get_workbench_lead_ids(client, token)
    assert status == 200
    
    assert lead_id_1 not in returned_ids
    assert lead_id_2 in returned_ids
