from abc import ABC, abstractmethod
from typing import Any, Optional

class IAIProvider(ABC):
    """
    Abstract Base Class defining the contract for all AI providers.
    Ensures business logic is agnostic of the underlying AI API.
    """

    @abstractmethod
    async def generate_text(self, prompt: str, context: Optional[dict[str, Any]] = None) -> str:
        """Generates a raw text response given a prompt and optional context."""
        pass

    @abstractmethod
    async def generate_structured_data(self, prompt: str, context: Optional[dict[str, Any]] = None) -> dict:
        """Generates structured JSON data given a prompt and optional context."""
        pass
