import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.security import create_access_token
from app.db.models import SignalInterceptORM
import uuid
import datetime

def _get_op_by_role(role: str, db: Session):
    op = db.execute(text("SELECT id, district_id FROM operators WHERE role = :role LIMIT 1"), {"role": role}).fetchone()
    if not op:
        pytest.skip(f"No operator found for role {role}")
    return op[0], op[1]

def _create_test_signal(db: Session, case_id: str, linked_case_str: str = "LEGACY_STRING") -> str:
    sig_id = str(uuid.uuid4())
    sig = SignalInterceptORM(
        id=sig_id,
        case_id=case_id,
        source="TEST_SOURCE",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        linked_case=linked_case_str,
        confidence=90
    )
    db.add(sig)
    db.flush()
    return sig_id

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

def test_signal_rbac_command_role(db_session, client):
    op_id, op_district = _get_op_by_role("command", db_session)
    case = db_session.execute(text("SELECT id FROM cases LIMIT 1")).fetchone()
    if not case:
        pytest.skip("No cases found")
        
    sig_id = _create_test_signal(db_session, case[0])
    
    token = create_access_token(str(op_id), role="command")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id in returned_ids

def test_signal_rbac_command_role_orphan(db_session, client):
    op_id, op_district = _get_op_by_role("command", db_session)
    sig_id = _create_test_signal(db_session, None)
    
    token = create_access_token(str(op_id), role="command")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id in returned_ids

def test_signal_rbac_analyst_same_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    case_id = _create_test_case_in_district(db_session, op_district)
    sig_id = _create_test_signal(db_session, case_id)
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id in returned_ids

def test_signal_rbac_analyst_other_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
    case_id = _create_test_case_in_district(db_session, other_dist[0])
    sig_id = _create_test_signal(db_session, case_id)
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id not in returned_ids

def test_signal_rbac_field_same_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    case_id = _create_test_case_in_district(db_session, op_district)
    sig_id = _create_test_signal(db_session, case_id)
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id in returned_ids

def test_signal_rbac_field_other_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    if not other_dist:
        pytest.skip("No other district found")
    case_id = _create_test_case_in_district(db_session, other_dist[0])
    sig_id = _create_test_signal(db_session, case_id)
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id not in returned_ids

def test_signal_rbac_analyst_orphan_denial(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    sig_id = _create_test_signal(db_session, None)
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id not in returned_ids

def test_signal_rbac_field_orphan_denial(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    sig_id = _create_test_signal(db_session, None)
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id not in returned_ids

def test_signal_rbac_unauthorized_role(db_session, client):
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
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 403

def test_signal_rls_does_not_use_legacy_string(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    other_dist = db_session.execute(text("SELECT id FROM districts WHERE id != :did LIMIT 1"), {"did": op_district}).fetchone()
    
    case_out = _create_test_case_in_district(db_session, other_dist[0])
    
    # Create signal with case outside jurisdiction, but legacy string matches operator's district string
    # Legacy string should not grant access
    sig_id = _create_test_signal(db_session, case_out, linked_case_str=op_district)
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/analytics/signal-intelligence", headers=headers)
    assert response.status_code == 200
    returned_ids = [s["id"] for s in response.json()]
    assert sig_id not in returned_ids
