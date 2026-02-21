"""
NeuroSync AI — Abstract base class for LLM providers.

Ensures Groq and OpenAI have identical interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Standardized message format."""

    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Standardized response format."""

    content: str
    tokens_used: int
    model: str
    provider: str
    finish_reason: str


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Implementations: GroqProvider, OpenAIProvider
    """

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.provider_name = "base"

    @abstractmethod
    def chat_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> LLMResponse:
        """Generate chat completion. MUST be implemented by all providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and accessible."""

    def get_provider_name(self) -> str:
        """Return provider name for logging."""
        return self.provider_name
