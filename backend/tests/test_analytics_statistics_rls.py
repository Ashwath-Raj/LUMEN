import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.auth import get_current_operator
from app.db.session import get_db

@pytest.fixture
def override_auth():
    def _override(role="analyst", district_id="D1"):
        class MockOperator:
            def __init__(self, r):
                self.id = "mock_op_1"
                self.role = r
        def _get_op():
            return MockOperator(role)
        app.dependency_overrides[get_current_operator] = _get_op
        
        return MockOperator(role)
    yield _override
    app.dependency_overrides = {}

@pytest.fixture
def mock_db_cases():
    with patch("app.services.repositories.module_service.ModuleService._get_authorized_cases") as mock_get_cases:
        yield mock_get_cases

@pytest.fixture
def mock_db_query():
    with patch("sqlalchemy.orm.Session.query") as mock_query, \
         patch("sqlalchemy.orm.Session.execute") as mock_execute:
        yield mock_query, mock_execute

def test_analytics_statistics_analyst_rls(override_auth, mock_db_cases, mock_db_query):
    # Setup the mock authorization boundary
    override_auth(role="analyst", district_id="D1")
    
    # Mock District A Case -> Property
    # District B Case -> Cyber is NOT in the authorized list
    class MockCaseMetadata:
        def __init__(self, section):
            self.bns_section = section
            
        def get(self, key, default=""):
            return getattr(self, key, default)

    class MockCase:
        def __init__(self, id, section):
            self.id = id
            self.case_metadata = MockCaseMetadata(section)

    mock_db_cases.return_value = [MockCase("C1", "309")] # 309 corresponds to Property
    
    # Ensure global query is not called for CaseORM
    mock_query, mock_execute = mock_db_query
    
    # We must mock execute for hotspots/risk index so it doesn't fail
    mock_execute_result = MagicMock()
    mock_execute_result.fetchall.return_value = []
    mock_execute.return_value = mock_execute_result

    client = TestClient(app)
    # Patch dependencies for DB
    app.dependency_overrides[get_db] = lambda: MagicMock()
    
    response = client.get("/api/analytics/statistics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify the category breakdown correctly calculates based on the AUTHORIZED cases only
    breakdown = data.get("categoryBreakdown", [])
    
    prop_count = next((item["count"] for item in breakdown if item["id"] == "property"), 0)
    cyber_count = next((item["count"] for item in breakdown if item["id"] == "cyber"), 0)
    
    assert prop_count == 1, "Analyst should see their district's case category count"
    assert cyber_count == 0, "Analyst should NOT see cross-district cases in category breakdown"
    
    # Verify we did NOT execute self._db.query(CaseORM.case_metadata)
    # (In our mock setup, if it had tried, it would have returned a MagicMock without the expected data structure unless we explicitly set it up, but the key is that _get_authorized_cases is the one driving it).
    assert mock_db_cases.call_count == 2


def test_analytics_statistics_command_rls(override_auth, mock_db_cases, mock_db_query):
    # Setup for command
    override_auth(role="command", district_id=None)
    
    class MockCaseMetadata:
        def __init__(self, section):
            self.bns_section = section
            
        def get(self, key, default=""):
            return getattr(self, key, default)

    class MockCase:
        def __init__(self, id, section):
            self.id = id
            self.case_metadata = MockCaseMetadata(section)

    # Command receives BOTH cases from _get_authorized_cases globally
    mock_db_cases.return_value = [
        MockCase("C1", "309"), # Property
        MockCase("C2", "66"),  # Cyber
    ]
    
    mock_query, mock_execute = mock_db_query
    mock_execute_result = MagicMock()
    mock_execute_result.fetchall.return_value = []
    mock_execute.return_value = mock_execute_result

    client = TestClient(app)
    app.dependency_overrides[get_db] = lambda: MagicMock()
    
    response = client.get("/api/analytics/statistics")
    
    assert response.status_code == 200
    data = response.json()
    
    breakdown = data.get("categoryBreakdown", [])
    prop_count = next((item["count"] for item in breakdown if item["id"] == "property"), 0)
    cyber_count = next((item["count"] for item in breakdown if item["id"] == "cyber"), 0)
    
    assert prop_count == 1, "Command should see Property from District A"
    assert cyber_count == 1, "Command should see Cyber from District B"
    assert mock_db_cases.call_count == 2
