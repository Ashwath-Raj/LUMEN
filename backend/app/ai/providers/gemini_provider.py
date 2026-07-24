import json
import logging
from typing import Any, Optional
from google import genai
from google.genai.types import GenerateContentConfig
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time

class CircuitBreakerOpenError(Exception):
    pass

from app.core.config import settings
from app.ai.interfaces.ai_provider import IAIProvider
from app.ai.providers.mock_provider import MockProvider
from app.ai.utils.json_parser import extract_json_from_text

logger = logging.getLogger(__name__)

class GeminiProvider(IAIProvider):
    """
    Live Gemini Provider using google-genai SDK.
    Upgraded for Phase 4 to natively support Pydantic response schemas for hallucination prevention.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model_name = settings.GEMINI_MODEL
        
        # Initialize GenAI Client
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None
        else:
            self.client = None
            
        self.circuit_open_until = 0.0
        self.cooldown_seconds = float(getattr(settings, "GEMINI_COOLDOWN_SECONDS", 60.0))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, Exception)),
        reraise=True
    )
    async def _execute_gemini_request(self, prompt: str, system_instruction: Optional[str] = None, response_schema: Any = None) -> str:
        kwargs = {"temperature": 0.2}
        if system_instruction:
            kwargs["system_instruction"] = system_instruction
            
        if response_schema:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = response_schema
            
        config = GenerateContentConfig(**kwargs)
            
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return response.text

    async def _call_gemini_api(self, prompt: str, system_instruction: Optional[str] = None, response_schema: Any = None) -> str:
        if not self.client:
            raise ValueError("Gemini API key is not configured or client failed to initialize.")
            
        if time.time() < self.circuit_open_until:
            raise CircuitBreakerOpenError("Circuit is open due to recent 429 Quota Exhaustion.")
            
        try:
            result = await self._execute_gemini_request(prompt, system_instruction, response_schema)
            self.circuit_open_until = 0.0
            return result
        except APIError as e:
            if e.code == 429:
                self.circuit_open_until = time.time() + self.cooldown_seconds
                raise CircuitBreakerOpenError(f"429 Quota Exhaustion reached. Opening circuit breaker for {self.cooldown_seconds}s.")
            raise
        except Exception as e:
            if "429" in str(e):
                self.circuit_open_until = time.time() + self.cooldown_seconds
                raise CircuitBreakerOpenError(f"429 Quota Exhaustion reached. Opening circuit breaker for {self.cooldown_seconds}s.")
            raise

    async def generate_text(self, prompt: str, context: Optional[dict[str, Any]] = None) -> str:
        """Generates a raw text response given a prompt and optional context."""
        try:
            system_instruction = context.get("system_prompt") if context else None
            return await self._call_gemini_api(prompt, system_instruction)
        except Exception as e:
            logger.error(f"Gemini API text generation failed: {e}. No mock fallback allowed.")
            raise

    async def generate_structured_data(self, prompt: str, context: Optional[dict[str, Any]] = None) -> dict:
        """Generates structured JSON data natively using response_schema."""
        system_instruction = context.get("system_prompt") if context else None
        response_schema = context.get("response_schema") if context else None
        
        try:
            raw_response = await self._call_gemini_api(prompt, system_instruction, response_schema)
        except Exception as e:
            logger.error(f"Gemini API structured generation failed: {e}. No mock fallback allowed.")
            raise
            
        try:
            return extract_json_from_text(raw_response)
        except json.JSONDecodeError:
            strict_prompt = prompt + "\n\nCRITICAL INSTRUCTION: You must return ONLY valid, parseable JSON."
            try:
                raw_response_retry = await self._call_gemini_api(strict_prompt, system_instruction, response_schema)
                return extract_json_from_text(raw_response_retry)
            except Exception as e:
                logger.error(f"Gemini API strict JSON parsing failed on retry: {e}. No mock fallback allowed.")
                raise
