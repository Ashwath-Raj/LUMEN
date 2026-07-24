"""
NOTE: Tests the deleted legacy DB models (lumen.db.models.legacy_models),
the deleted legacy Neo4j service, and the deleted Gemini AI service.
Expected to fail import/collection until these subsystems are rebuilt in
later LUMEN_MASTER_SPEC_V3 sessions (Session 2 for the canonical DB
schema, Session 14 for the QuickML AI orchestrator). Left as-is (not
deleted, not patched) per the sanitation-pass scope.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from lumen.db.models.legacy_models import (
    OperatorORM, UnitORM, DistrictORM, CaseORM, InvestigationReportORM,
    FIRORM
)
import uuid
import datetime
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_external_calls(monkeypatch):
    from unittest.mock import AsyncMock
    monkeypatch.setattr("lumen.graph.legacy_neo4j_service.Neo4jGraphService.get_case_network", MagicMock(return_value={"nodes": [], "edges": []}))
    monkeypatch.setattr("lumen.ai.services.ai_service.AIService.summarise_intelligence", AsyncMock(return_value="Mock summary"))
    monkeypatch.setattr("lumen.ai.services.ai_service.AIService.generate_report", AsyncMock(return_value="Mock report"))


from lumen.db.session import SessionLocal

@pytest.fixture
def real_client():
    from main import app
    from fastapi.testclient import TestClient
    from lumen.db.session import get_db
    app.dependency_overrides.pop(get_db, None)
    return TestClient(app)

@pytest.fixture
def test_data():
    db_session = SessionLocal()
    
    # Idempotent cleanup first
    db_session.query(FIRORM).filter(FIRORM.case_id.in_(["case-d1-active", "case-d2-active", "case-orphan"])).delete()
    db_session.query(InvestigationReportORM).filter(InvestigationReportORM.case_id.in_(["case-d1-active", "case-d2-active", "case-orphan"])).delete()
    db_session.query(CaseORM).filter(CaseORM.id.in_(["case-d1-active", "case-d1-closed", "case-d2-active", "case-d2-closed", "case-orphan", "case-broken"])).delete()
    db_session.query(UnitORM).filter(UnitORM.id.in_(["u-case-1", "u-case-2", "u-broken"])).delete()
    db_session.query(OperatorORM).filter(OperatorORM.id.in_(["test-cmd-case", "test-ana1-case", "test-ana2-case", "test-fld1-case"])).delete()
    db_session.query(DistrictORM).filter(DistrictORM.id.in_(["d-case-1", "d-case-2"])).delete()
    db_session.commit()
    
    # Operators
    command = OperatorORM(id="test-cmd-case", name="Cmd", role="command", clearance=5, status="ACTIVE", operator_id="CMD-1", unit="Test Unit", rank="Inspector", date_of_entry=datetime.date.today(), assigned_unit="Test", biometric_hash="hash")
    analyst1 = OperatorORM(id="test-ana1-case", name="Ana1", role="analyst", clearance=3, status="ACTIVE", operator_id="ANA-1", unit="Test Unit", rank="Inspector", date_of_entry=datetime.date.today(), assigned_unit="Test", biometric_hash="hash")
    analyst2 = OperatorORM(id="test-ana2-case", name="Ana2", role="analyst", clearance=3, status="ACTIVE", operator_id="ANA-2", unit="Test Unit", rank="Inspector", date_of_entry=datetime.date.today(), assigned_unit="Test", biometric_hash="hash")
    field1 = OperatorORM(id="test-fld1-case", name="Fld1", role="field", clearance=2, status="ACTIVE", operator_id="FLD-1", unit="Test Unit", rank="Inspector", date_of_entry=datetime.date.today(), assigned_unit="Test", biometric_hash="hash")
    
    db_session.add_all([command, analyst1, analyst2, field1])
    db_session.commit()

    # Districts
    dist1 = DistrictORM(id="d-case-1", name="North District")
    dist2 = DistrictORM(id="d-case-2", name="South District")
    db_session.add_all([dist1, dist2])
    db_session.commit()
    
    # Assign districts to operators
    analyst1.district_id = "d-case-1"
    field1.district_id = "d-case-1"
    analyst2.district_id = "d-case-2"
    
    # Units
    u1 = UnitORM(id="u-case-1", name="North Station", district_id="d-case-1")
    u2 = UnitORM(id="u-case-2", name="South Station", district_id="d-case-2")
    db_session.add_all([u1, u2])
    db_session.commit()

    # Cases
    now = datetime.datetime.now()
    c_d1_active = CaseORM(id="case-d1-active", police_station_id="u-case-1", status="Under Investigation", label="D1 Active", updated_at=now)
    c_d1_closed = CaseORM(id="case-d1-closed", police_station_id="u-case-1", status="Closed", label="D1 Closed", updated_at=now)
    
    c_d2_active = CaseORM(id="case-d2-active", police_station_id="u-case-2", status="Under Investigation", label="D2 Active", updated_at=now)
    c_d2_closed = CaseORM(id="case-d2-closed", police_station_id="u-case-2", status="Closed", label="D2 Closed", updated_at=now)
    
    # Orphan case (no unit)
    c_orphan = CaseORM(id="case-orphan", police_station_id=None, status="Under Investigation", label="Orphan", updated_at=now)
    
    # Broken unit chain case
    u_broken = UnitORM(id="u-broken", name="Broken Unit", district_id=None)
    db_session.add(u_broken)
    db_session.commit()
    c_broken = CaseORM(id="case-broken", police_station_id="u-broken", status="Under Investigation", label="Broken Unit", updated_at=now)
    
    db_session.add_all([c_d1_active, c_d1_closed, c_d2_active, c_d2_closed, c_orphan, c_broken])
    db_session.commit()
    
    # Investigation Reports
    rep1 = InvestigationReportORM(id=str(uuid.uuid4()), case_id="case-d1-active", title="D1 Report")
    rep2 = InvestigationReportORM(id=str(uuid.uuid4()), case_id="case-d2-active", title="D2 Report")
    rep_orphan = InvestigationReportORM(id=str(uuid.uuid4()), case_id="case-orphan", title="Orphan Report")
    db_session.add_all([rep1, rep2, rep_orphan])
    
    # Add FIRs for dashboard counts
    f1 = FIRORM(id=str(uuid.uuid4()), case_id="case-d1-active", fir_number="FIR D1", district="D1", year="2026")
    f2 = FIRORM(id=str(uuid.uuid4()), case_id="case-d2-active", fir_number="FIR D2", district="D2", year="2026")
    f3 = FIRORM(id=str(uuid.uuid4()), case_id="case-orphan", fir_number="FIR Orphan", district="D3", year="2026")
    db_session.add_all([f1, f2, f3])
    db_session.commit()
    db_session.close()
    
    db_session.close()
    
    try:
        yield {
            "command": command.id,
            "analyst1": analyst1.id,
            "analyst2": analyst2.id,
            "field1": field1.id,
            "c_d1_active": c_d1_active.id,
            "c_d1_closed": c_d1_closed.id,
            "c_d2_active": c_d2_active.id,
            "c_d2_closed": c_d2_closed.id,
            "c_orphan": c_orphan.id,
            "c_broken": c_broken.id,
            "rep1": rep1.id,
            "rep2": rep2.id,
            "rep_orphan": rep_orphan.id,
            "f1": f1.id,
            "f2": f2.id,
            "f3": f3.id,
        }
    finally:
        db_session = SessionLocal()
        db_session.query(FIRORM).filter(FIRORM.id.in_([f1.id, f2.id, f3.id])).delete()
        db_session.query(InvestigationReportORM).filter(InvestigationReportORM.id.in_([rep1.id, rep2.id, rep_orphan.id])).delete()
        db_session.query(CaseORM).filter(CaseORM.id.in_([c_d1_active.id, c_d1_closed.id, c_d2_active.id, c_d2_closed.id, c_orphan.id, c_broken.id])).delete()
        db_session.query(UnitORM).filter(UnitORM.id.in_([u1.id, u2.id, u_broken.id])).delete()
        db_session.query(OperatorORM).filter(OperatorORM.id.in_([command.id, analyst1.id, analyst2.id, field1.id])).delete()
        db_session.query(DistrictORM).filter(DistrictORM.id.in_([dist1.id, dist2.id])).delete()
        db_session.commit()
        db_session.close()


def get_token(op_id, role="command"):
    from lumen.identity.security import create_access_token
    return create_access_token(op_id, role)


# --- Direct Case Access ---

def test_direct_case_access_command(real_client, test_data):
    token = get_token(test_data["command"])
    headers = {"Authorization": f"Bearer {token}"}
    
    res1 = real_client.get(f"/api/investigation/cases/{test_data['c_d1_active']}", headers=headers)
    assert res1.status_code == 200
    
    res_orphan = real_client.get(f"/api/investigation/cases/{test_data['c_orphan']}", headers=headers)
    assert res_orphan.status_code == 200

def test_direct_case_access_analyst(real_client, test_data):
    print("test_direct_case_access_analyst started")
    token = get_token(test_data["analyst1"], role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("res1 starting")
    # Same district
    res1 = real_client.get(f"/api/investigation/cases/{test_data['c_d1_active']}", headers=headers)
    print(f"res1 done: {res1.status_code}")
    assert res1.status_code == 200
    
    print("res2 starting")
    # Cross district
    res2 = real_client.get(f"/api/investigation/cases/{test_data['c_d2_active']}", headers=headers)
    print(f"res2 done: {res2.status_code}")
    assert res2.status_code == 404
    
    print("res3 starting")
    # Orphan
    res3 = real_client.get(f"/api/investigation/cases/{test_data['c_orphan']}", headers=headers)
    print(f"res3 done: {res3.status_code}")
    assert res3.status_code == 404
    
    print("res4 starting")
    # Broken Unit
    res4 = real_client.get(f"/api/investigation/cases/{test_data['c_broken']}", headers=headers)
    print(f"res4 done: {res4.status_code}")
    assert res4.status_code == 404

def test_direct_case_access_field(real_client, test_data):
    token = get_token(test_data["field1"], role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Same district
    res1 = real_client.get(f"/api/investigation/cases/{test_data['c_d1_active']}", headers=headers)
    assert res1.status_code == 200
    
    # Cross district
    res2 = real_client.get(f"/api/investigation/cases/{test_data['c_d2_active']}", headers=headers)
    assert res2.status_code == 404
    
def test_direct_case_access_invalid_id(real_client, test_data):
    token = get_token(test_data["analyst1"], role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = real_client.get(f"/api/investigation/cases/nonexistent", headers=headers)
    assert res.status_code == 404

# --- Case Reports Access ---

def test_case_reports_access_analyst(real_client, test_data):
    token = get_token(test_data["analyst1"], role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Same district
    res1 = real_client.get(f"/api/investigation/cases/{test_data['c_d1_active']}/reports", headers=headers)
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)
    
    # Cross district
    res2 = real_client.get(f"/api/investigation/cases/{test_data['c_d2_active']}/reports", headers=headers)
    assert res2.status_code == 404
    
    # Orphan
    res3 = real_client.get(f"/api/investigation/cases/{test_data['c_orphan']}/reports", headers=headers)
    assert res3.status_code == 404

def test_case_reports_access_command(real_client, test_data):
    token = get_token(test_data["command"])
    headers = {"Authorization": f"Bearer {token}"}
    
    res = real_client.get(f"/api/investigation/cases/{test_data['c_d2_active']}/reports", headers=headers)
    assert res.status_code == 200

# --- Investigation Archive ---

def test_investigation_archive(real_client, test_data):
    headers_cmd = {"Authorization": f"Bearer {get_token(test_data['command'], role='command')}"}
    headers_a1 = {"Authorization": f"Bearer {get_token(test_data['analyst1'], role='analyst')}"}
    
    res_cmd = real_client.get("/api/investigation/archive", headers=headers_cmd)
    assert res_cmd.status_code == 200
    # Command should see D1 Closed and D2 Closed
    ids_cmd = [c["id"] for c in res_cmd.json()]
    assert test_data["c_d1_closed"] in ids_cmd
    assert test_data["c_d2_closed"] in ids_cmd
    
    res_a1 = real_client.get("/api/investigation/archive", headers=headers_a1)
    assert res_a1.status_code == 200
    ids_a1 = [c["id"] for c in res_a1.json()]
    assert test_data["c_d1_closed"] in ids_a1
    assert test_data["c_d2_closed"] not in ids_a1

# --- Tactical Overview ---

def test_tactical_overview(real_client, test_data):
    headers_cmd = {"Authorization": f"Bearer {get_token(test_data['command'], role='command')}"}
    headers_a1 = {"Authorization": f"Bearer {get_token(test_data['analyst1'], role='analyst')}"}
    
    res_cmd = real_client.get("/api/operations/tactical-overview", headers=headers_cmd)
    assert res_cmd.status_code == 200
    ids_cmd = [i["id"] for i in res_cmd.json()["incidentQueue"]]
    assert test_data["c_d1_active"] in ids_cmd
    assert test_data["c_d2_active"] in ids_cmd
    
    res_a1 = real_client.get("/api/operations/tactical-overview", headers=headers_a1)
    assert res_a1.status_code == 200
    ids_a1 = [i["id"] for i in res_a1.json()["incidentQueue"]]
    assert test_data["c_d1_active"] in ids_a1
    assert test_data["c_d2_active"] not in ids_a1

# --- Composite Dashboard Aggregations ---

def test_dashboard_summary_metrics(real_client, test_data):
    headers_cmd = {"Authorization": f"Bearer {get_token(test_data['command'], role='command')}"}
    headers_a1 = {"Authorization": f"Bearer {get_token(test_data['analyst1'], role='analyst')}"}
    
    res_cmd = real_client.get("/api/dashboard/summary", headers=headers_cmd)
    assert res_cmd.status_code == 200
    cmd_metrics = res_cmd.json()
    # Command sees all cases (D1 active+closed, D2 active+closed, orphan, broken = 6)
    assert cmd_metrics["totalCrimes"]["value"] == 6
    
    res_a1 = real_client.get("/api/dashboard/summary", headers=headers_a1)
    assert res_a1.status_code == 200
    a1_metrics = res_a1.json()
    # Analyst 1 sees only D1 active+closed (2 cases)
    assert a1_metrics["totalCrimes"]["value"] == 2

def test_analytics_statistics(real_client, test_data):
    headers_a1 = {"Authorization": f"Bearer {get_token(test_data['analyst1'], role='analyst')}"}
    res = real_client.get("/api/analytics/statistics", headers=headers_a1)
    assert res.status_code == 200
    data = res.json()
    total_crimes_entry = next((i for i in data["overview"] if i["id"] == "total-incidents"), None)
    assert total_crimes_entry is not None
    assert int(total_crimes_entry["value"]) == 2
    assert res1.status_code == 200
    
    res_orphan = client.get(f"/api/investigation/cases/{test_data['c_orphan']}", headers=headers)
    assert res_orphan.status_code == 200

def test_direct_case_access_analyst(client, test_data):
    token = get_token(test_data["analyst1"], role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Same district
    res1 = client.get(f"/api/investigation/cases/{test_data['c_d1_active']}", headers=headers)
    assert res1.status_code == 200
    
    # Cross district
    res2 = client.get(f"/api/investigation/cases/{test_data['c_d2_active']}", headers=headers)
    assert res2.status_code == 404
    
    # Orphan
    res3 = client.get(f"/api/investigation/cases/{test_data['c_orphan']}", headers=headers)
    assert res3.status_code == 404
    
    # Broken Unit
    res4 = client.get(f"/api/investigation/cases/{test_data['c_broken']}", headers=headers)
    assert res4.status_code == 404

def test_direct_case_access_field(client, test_data):
    token = get_token(test_data["field1"], role="field")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Same district
    res1 = client.get(f"/api/investigation/cases/{test_data['c_d1_active']}", headers=headers)
    assert res1.status_code == 200
    
    # Cross district
    res2 = client.get(f"/api/investigation/cases/{test_data['c_d2_active']}", headers=headers)
    assert res2.status_code == 404
    
def test_direct_case_access_invalid_id(client, test_data):
    token = get_token(test_data["analyst1"], role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get(f"/api/investigation/cases/nonexistent", headers=headers)
    assert res.status_code == 404

# --- Case Reports Access ---

def test_case_reports_access_analyst(client, test_data):
    token = get_token(test_data["analyst1"], role="analyst")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Same district
    res1 = client.get(f"/api/investigation/cases/{test_data['c_d1_active']}/reports", headers=headers)
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)
    
    # Cross district
    res2 = client.get(f"/api/investigation/cases/{test_data['c_d2_active']}/reports", headers=headers)
    assert res2.status_code == 404
    
    # Orphan
    res3 = client.get(f"/api/investigation/cases/{test_data['c_orphan']}/reports", headers=headers)
    assert res3.status_code == 404

def test_case_reports_access_command(client, test_data):
    token = get_token(test_data["command"])
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get(f"/api/investigation/cases/{test_data['c_d2_active']}/reports", headers=headers)
    assert res.status_code == 200

# --- Investigation Archive ---

def test_investigation_archive(client, test_data):
    headers_cmd = {"Authorization": f"Bearer {get_token(test_data['command'], role='command')}"}
    headers_a1 = {"Authorization": f"Bearer {get_token(test_data['analyst1'], role='analyst')}"}
    
    res_cmd = client.get("/api/investigation/archive", headers=headers_cmd)
    assert res_cmd.status_code == 200
    # Command should see D1 Closed and D2 Closed
    ids_cmd = [c["id"] for c in res_cmd.json()]
    assert test_data["c_d1_closed"] in ids_cmd
    assert test_data["c_d2_closed"] in ids_cmd
    
    res_a1 = client.get("/api/investigation/archive", headers=headers_a1)
    assert res_a1.status_code == 200
    ids_a1 = [c["id"] for c in res_a1.json()]
    assert test_data["c_d1_closed"] in ids_a1
    assert test_data["c_d2_closed"] not in ids_a1

# --- Tactical Overview ---

def test_tactical_overview(client, test_data):
    headers_cmd = {"Authorization": f"Bearer {get_token(test_data['command'], role='command')}"}
    headers_f1 = {"Authorization": f"Bearer {get_token(test_data['field1'], role='field')}"}
    
    res_cmd = client.get("/api/operations/tactical-overview", headers=headers_cmd)
    assert res_cmd.status_code == 200
    ids_cmd = [i["id"] for i in res_cmd.json()["incidentQueue"]]
    assert test_data["c_d1_active"] in ids_cmd
    assert test_data["c_d2_active"] in ids_cmd
    
    res_f1 = client.get("/api/operations/tactical-overview", headers=headers_f1)
    assert res_f1.status_code == 200
    ids_f1 = [i["id"] for i in res_f1.json()["incidentQueue"]]
    assert test_data["c_d1_active"] in ids_f1
    assert test_data["c_d2_active"] not in ids_f1

# --- Composite Dashboard Aggregations ---

def test_dashboard_summary_metrics(client, test_data):
    headers_cmd = {"Authorization": f"Bearer {get_token(test_data['command'], role='command')}"}
    headers_a1 = {"Authorization": f"Bearer {get_token(test_data['analyst1'], role='analyst')}"}
    
    res_cmd = client.get("/api/dashboard/summary", headers=headers_cmd)
    assert res_cmd.status_code == 200
    cmd_metrics = res_cmd.json()
    # Command sees all cases 
    assert cmd_metrics["totalCrimes"]["value"] >= 4
    
    res_a1 = client.get("/api/dashboard/summary", headers=headers_a1)
    assert res_a1.status_code == 200
    a1_metrics = res_a1.json()
    # Analyst sees fewer cases than command
    assert a1_metrics["totalCrimes"]["value"] < cmd_metrics["totalCrimes"]["value"]

def test_analytics_statistics(client, test_data):
    headers_a1 = {"Authorization": f"Bearer {get_token(test_data['analyst1'], role='analyst')}"}
    res = client.get("/api/analytics/statistics", headers=headers_a1)
    assert res.status_code == 200
    data = res.json()
    total_crimes_entry = next((i for i in data["overview"] if i["id"] == "total-incidents"), None)
    assert total_crimes_entry is not None
    assert int(total_crimes_entry["value"]) == 2
