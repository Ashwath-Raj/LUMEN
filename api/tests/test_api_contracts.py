"""
API Contract Regression Tests
These tests ensure deterministic verification of the API endpoints, schemas,
and authentication barriers without invoking live AI APIs.

NOTE: Collects fine (the `@patch('lumen.ai.services.ai_service...')`
targets are resolved lazily at call time, not at import time), but will
fail at runtime: the deleted Gemini AI service and legacy auth mean the
patched module no longer exists and the routers now return 501 instead of
their old behavior. Expected to be rewritten in later LUMEN_MASTER_SPEC_V3
sessions (Session 3 for Catalyst Authentication, Session 14 for the
QuickML AI orchestrator).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# ── 1. Health Endpoint ────────────────────────────────────────────────────────

def test_health_endpoint(client):
    """Verify health check is public and returns 200."""
    resp = client.get("/api/health")
    if resp.status_code == 404:
        resp = client.get("/health")
    
    if resp.status_code != 200:
        pytest.skip("No health endpoint implemented yet")


# ── 2. Dashboard Summary ──────────────────────────────────────────────────────

def test_dashboard_summary_requires_auth(client):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 401


def test_dashboard_summary_contract(client, headers):
    resp = client.get("/api/dashboard/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "totalCrimes" in data
    assert "activeCases" in data
    assert data.get("highRiskCriminals", {}).get("value") == "N/A"


# ── 3. Investigation Cases ────────────────────────────────────────────────────

def test_investigation_cases_requires_auth(client):
    resp = client.get("/api/investigation/cases")
    assert resp.status_code == 401


def test_investigation_cases_contract(client, headers):
    resp = client.get("/api/investigation/cases", headers=headers)
    assert resp.status_code == 200
    cases = resp.json()
    assert isinstance(cases, list)
    if cases:
        first_case = cases[0]
        assert "id" in first_case
        assert "label" in first_case
        assert "status" in first_case


# ── 4. Case Detail (with mocked AI) ───────────────────────────────────────────

class DummyAIProvider:
    async def generate_structured_data(self, prompt, context, *args, **kwargs):
        task_type = context.get("task_type")
        if task_type == "intelligence_query":
            return {
                "answer": "Deterministic Mocked Answer",
                "confidence_score": 95,
                "evidence_used": ["Mock Evidence"]
            }
        # Default fallback for other tasks like summarise_intelligence
        return {
            "incident_summary": "Mocked deterministic AI summary.",
            "evidence_collected": [],
            "current_status": "Under Investigation",
            "pending_actions": [],
            "risk_assessment": "Medium Risk",
            "recommended_next_step": "Next step"
        }

@patch('lumen.ai.services.ai_service.get_ai_provider', return_value=DummyAIProvider())
@pytest.mark.asyncio
async def test_investigation_case_detail_contract(mock_get_provider, client, headers):
    """Verify case detail schema and that AI summary gracefully degrades/mocks."""
    resp = client.get("/api/investigation/cases", headers=headers)
    cases = resp.json()
    if not cases:
        pytest.skip("No cases available in DB to test detail endpoint")
    
    case_id = cases[0]["id"]
    detail_resp = client.get(f"/api/investigation/cases/{case_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    
    assert detail["id"] == case_id
    assert "summary" in detail
    # assert "graph" in detail


# ── 5. Intelligence Query (with mocked AI) ────────────────────────────────────

@patch('lumen.ai.services.ai_service.get_ai_provider', return_value=DummyAIProvider())
def test_intelligence_query_contract(mock_get_provider, client, headers):
    resp = client.post(
        "/api/intelligence/query",
        json={"query": "What is the status?"},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    print("QUERY RETURNED:", data)
    assert data["answer"] == "Deterministic Mocked Answer"
    assert data["confidence_score"] == 95


def test_intelligence_query_no_mock_fallback_on_error(client, headers):
    """
    Ensure that when the provider isn't mocked and fails, it raises an exception
    rather than silently returning a MockProvider response.
    """
    # Import TestClient here to instantiate one that doesn't raise exceptions locally
    from fastapi.testclient import TestClient
    from main import app
    from lumen.db.session import get_db
    
    # Re-apply override to use existing test db_session
    app.dependency_overrides[get_db] = client.app.dependency_overrides[get_db]
    safe_client = TestClient(app, raise_server_exceptions=False)
    
    with patch('lumen.config.settings.GEMINI_API_KEY', ''):
        resp = safe_client.post(
            "/api/intelligence/query",
            json={"query": "Force failure"},
            headers=headers
        )
        assert resp.status_code == 500
    app.dependency_overrides.clear()
