"""
NOTE: Tests the deleted Gemini provider (lumen.ai.providers.gemini_provider).
Expected to fail import/collection until the QuickML AI orchestrator is
built in a later LUMEN_MASTER_SPEC_V3 session (Session 14). Left as-is
(not deleted, not patched) per the sanitation-pass scope.
"""
import pytest
import time
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from google.genai.errors import APIError
from lumen.ai.providers.gemini_provider import GeminiProvider, CircuitBreakerOpenError

@pytest.fixture
def gemini_provider():
    # Provide a dummy API key so the client initializes
    provider = GeminiProvider(api_key="dummy_key")
    provider.cooldown_seconds = 1.0 # Short cooldown for testing
    # Mock the internal client response
    provider.client = MagicMock()
    provider.client.aio.models.generate_content = AsyncMock()
    return provider

@pytest.mark.asyncio
async def test_circuit_breaker_normal_success(gemini_provider):
    # Mock normal response
    mock_response = MagicMock()
    mock_response.text = "Success response"
    gemini_provider.client.aio.models.generate_content.return_value = mock_response

    result = await gemini_provider.generate_text("test")
    assert result == "Success response"
    assert gemini_provider.circuit_open_until == 0.0

@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_429(gemini_provider):
    # Setup mock to raise APIError with code 429
    error = APIError("Quota exceeded", {})
    error.code = 429
    gemini_provider.client.aio.models.generate_content.side_effect = error

    with pytest.raises(CircuitBreakerOpenError):
        await gemini_provider.generate_text("test")

    # Circuit should now be open
    assert gemini_provider.circuit_open_until > time.time()

    # Subsequent request should fail fast without invoking the client
    gemini_provider.client.aio.models.generate_content.reset_mock()
    with pytest.raises(CircuitBreakerOpenError):
        await gemini_provider.generate_text("test")
    
    # Assert client wasn't called again due to fail-fast
    gemini_provider.client.aio.models.generate_content.assert_not_called()

@pytest.mark.asyncio
async def test_circuit_breaker_cooldown_and_retry(gemini_provider):
    # Open the circuit manually
    gemini_provider.circuit_open_until = time.time() + 0.1
    
    with pytest.raises(CircuitBreakerOpenError):
        await gemini_provider.generate_text("test")

    # Wait for cooldown
    await asyncio.sleep(0.15)

    # Setup mock for successful retry
    mock_response = MagicMock()
    mock_response.text = "Recovered response"
    gemini_provider.client.aio.models.generate_content.return_value = mock_response

    result = await gemini_provider.generate_text("test")
    assert result == "Recovered response"
    assert gemini_provider.circuit_open_until == 0.0

@pytest.mark.asyncio
async def test_circuit_breaker_ignores_non_429_errors(gemini_provider):
    error = APIError("Internal Server Error", {})
    error.code = 500
    gemini_provider.client.aio.models.generate_content.side_effect = error

    with pytest.raises(APIError):
        await gemini_provider.generate_text("test")

    # Circuit should NOT open for a 500 error
    assert gemini_provider.circuit_open_until == 0.0
