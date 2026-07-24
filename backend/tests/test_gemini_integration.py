"""
Optional Live Gemini Integration Tests
These tests run against the actual Gemini API and should be marked as integration tests.
They ensure the end-to-end connection works when a valid GEMINI_API_KEY is provided.
"""

import os
import pytest
from app.core.config import settings

# Only run these tests if GEMINI_API_KEY is configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not settings.GEMINI_API_KEY, reason="Live GEMINI_API_KEY not configured")
]


def test_live_intelligence_query(client, headers):
    """Test a real intelligence query against the Gemini API."""
    resp = client.post(
        "/api/intelligence/query",
        json={"query": "List the most frequent active crime type across all cases."},
        headers=headers
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "MockProvider" not in data["answer"]
    assert "DummyAIProvider" not in data["answer"]


def test_live_case_summarization(client, headers):
    """Test a real case summarization using the Gemini API."""
    resp = client.get("/api/investigation/cases", headers=headers)
    cases = resp.json()
    if not cases:
        pytest.skip("No cases available in DB to test detail endpoint")
    
    case_id = cases[0]["id"]
    detail_resp = client.get(f"/api/investigation/cases/{case_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    
    assert "summary" in detail
    assert isinstance(detail["summary"], str)
    
    import json
    summary_dict = json.loads(detail["summary"])
    assert "incident_summary" in summary_dict
