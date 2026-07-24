import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.security import create_access_token
from app.db.models import FIRORM
import uuid
import datetime

def _get_op_by_role(role: str, db: Session):
    op = db.execute(text("SELECT id, district_id FROM operators WHERE role = :role LIMIT 1"), {"role": role}).fetchone()
    if not op:
        pytest.skip(f"No {role} found to test RLS")
    return op[0], op[1]

def _create_test_fir(db: Session, case_id: str, extracted_entities=None):
    fir_id = str(uuid.uuid4())
    fir = FIRORM(
        id=fir_id,
        case_id=case_id,
        fir_number=f"FIR-{fir_id[:8]}",
        district="Mock",
        year="2026",
        extracted_entities=extracted_entities
    )
    db.add(fir)
    db.flush()
    return fir_id

def test_fir_rbac_command_role(db_session, client):
    op_id, op_district = _get_op_by_role("command", db_session)
    # Find any case
    case = db_session.execute(text("SELECT id FROM cases LIMIT 1")).fetchone()
    if not case:
        pytest.skip("No cases found")
    
    fir_id = _create_test_fir(db_session, case[0])
    
    token = create_access_token(str(op_id), role="command")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Command can access FIRs
    response = client.get(f"/api/investigation/fir-intelligence/{fir_id}", headers=headers)
    assert response.status_code == 200

def test_fir_rbac_analyst_same_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    
    case = db_session.execute(text(
        "SELECT c.id FROM cases c "
        "JOIN units u ON c.police_station_id = u.id "
        "WHERE u.district_id = :d LIMIT 1"
    ), {"d": op_district}).fetchone()
    if not case:
        pytest.skip("No case found in analyst jurisdiction")
        
    fir_id = _create_test_fir(db_session, case[0])
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/api/investigation/fir-intelligence/{fir_id}", headers=headers)
    assert response.status_code == 200

def test_fir_rbac_analyst_other_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("analyst", db_session)
    
    case = db_session.execute(text(
        "SELECT c.id FROM cases c "
        "JOIN units u ON c.police_station_id = u.id "
        "WHERE u.district_id != :d LIMIT 1"
    ), {"d": op_district}).fetchone()
    if not case:
        pytest.skip("No case found outside analyst jurisdiction")
        
    fir_id = _create_test_fir(db_session, case[0])
    
    token = create_access_token(str(op_id), role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/api/investigation/fir-intelligence/{fir_id}", headers=headers)
    assert response.status_code == 404

def test_fir_rbac_field_same_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    
    case = db_session.execute(text(
        "SELECT c.id FROM cases c "
        "JOIN units u ON c.police_station_id = u.id "
        "WHERE u.district_id = :d LIMIT 1"
    ), {"d": op_district}).fetchone()
    if not case:
        pytest.skip("No case found in field jurisdiction")
        
    fir_id = _create_test_fir(db_session, case[0])
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/api/investigation/fir-intelligence/{fir_id}", headers=headers)
    assert response.status_code == 200

def test_fir_rbac_field_other_jurisdiction(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    
    case = db_session.execute(text(
        "SELECT c.id FROM cases c "
        "JOIN units u ON c.police_station_id = u.id "
        "WHERE u.district_id != :d LIMIT 1"
    ), {"d": op_district}).fetchone()
    if not case:
        pytest.skip("No case found outside field jurisdiction")
        
    fir_id = _create_test_fir(db_session, case[0])
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/api/investigation/fir-intelligence/{fir_id}", headers=headers)
    assert response.status_code == 404

def test_fir_rbac_unauthorized_role(db_session, client):
    from app.db.models import OperatorORM
    op_id = "OP-AUDITOR"
    op = OperatorORM(
        id=op_id, operator_id=op_id, name="Auditor", rank="Civilian",
        role="auditor", status="ACTIVE", clearance="Level 1", unit="N/A", assigned_unit="N/A",
        date_of_entry="2026-07-23", biometric_hash="mock_hash"
    )
    db_session.add(op)
    db_session.flush()
    
    case = db_session.execute(text("SELECT id FROM cases LIMIT 1")).fetchone()
    fir_id = _create_test_fir(db_session, case[0])
    
    token = create_access_token(str(op_id), role="auditor")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/api/investigation/fir-intelligence/{fir_id}", headers=headers)
    assert response.status_code == 403

def test_fir_rls_inherits_case_jurisdiction(db_session, client):
    row = db_session.execute(text(
        "SELECT u.district_id, c.id FROM cases c "
        "JOIN units u ON c.police_station_id = u.id LIMIT 1"
    )).fetchone()
    if not row:
        pytest.skip("No cases found")
    dist_id, case_in_id = row
    
    case_out = db_session.execute(text(
        "SELECT c.id FROM cases c "
        "JOIN units u ON c.police_station_id = u.id "
        "WHERE u.district_id != :d LIMIT 1"
    ), {"d": dist_id}).fetchone()
    if not case_out:
        pytest.skip("No cases outside district")
        
    from app.db.models import OperatorORM
    op_id = "OP-TESTFIELD"
    op = OperatorORM(
        id=op_id, operator_id=op_id, name="Test Field", rank="Constable",
        role="field", status="ACTIVE", clearance="Level 1", unit="N/A", assigned_unit="N/A", district_id=dist_id,
        date_of_entry="2026-07-23", biometric_hash="mock_hash"
    )
    db_session.add(op)
    db_session.flush()
    
    import json
    entities = [{"type": "person", "name": "Test"}]
    fir_in_id = _create_test_fir(db_session, case_in_id, extracted_entities=entities)
    fir_out_id = _create_test_fir(db_session, case_out[0], extracted_entities=entities)
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/operations/suspects/ANY/records", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    returned_ids = {r["id"] for r in data}
    assert fir_in_id in returned_ids
    assert fir_out_id not in returned_ids

def test_fir_rls_does_not_use_legacy_district_string(db_session, client):
    op_id, op_district = _get_op_by_role("field", db_session)
    
    case_out = db_session.execute(text(
        "SELECT c.id FROM cases c "
        "JOIN units u ON c.police_station_id = u.id "
        "WHERE u.district_id != :d LIMIT 1"
    ), {"d": op_district}).fetchone()
    if not case_out:
        pytest.skip("No case outside district")
    
    fir_id = str(uuid.uuid4())
    fir = FIRORM(
        id=fir_id,
        case_id=case_out[0],
        fir_number=f"FIR-{fir_id[:8]}",
        district=op_district,
        year="2026"
    )
    db_session.add(fir)
    db_session.flush()
    
    token = create_access_token(str(op_id), role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get(f"/api/investigation/fir-intelligence/{fir_id}", headers=headers)
    assert response.status_code == 404
