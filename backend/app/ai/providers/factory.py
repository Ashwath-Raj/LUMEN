from app.core.config import settings
from app.ai.interfaces.ai_provider import IAIProvider
from app.ai.providers.mock_provider import MockProvider
from app.ai.providers.gemini_provider import GeminiProvider

def get_ai_provider() -> IAIProvider:
    """
    Factory function to select the active AI provider based on configuration.
    Ensures that business logic depends on the abstract IAIProvider, not concrete classes.
    """
    provider_type = settings.ACTIVE_AI_PROVIDER.lower()
    
    if provider_type == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
        
    raise ValueError(f"AI Provider '{provider_type}' is not supported or not configured. MockProvider fallback is disabled.")
