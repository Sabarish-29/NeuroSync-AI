"""
NeuroSync AI — Factory for creating LLM providers based on configuration.

Supports fallback from Groq -> OpenAI if primary fails.
"""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger

from neurosync.llm.base_provider import BaseLLMProvider


class LLMProviderFactory:
    """
    Creates and manages LLM providers with automatic fallback.

    Priority:
    1. Try configured provider (Groq or OpenAI)
    2. Fall back to alternative if available
    3. Raise error if none available
    """

    @staticmethod
    def create_provider(
        preferred_provider: Optional[str] = None,
        enable_fallback: bool = True,
    ) -> BaseLLMProvider:
        """
        Create LLM provider with fallback support.

        Args:
            preferred_provider: "groq" or "openai" (defaults to env var)
            enable_fallback: Try alternative provider if preferred fails

        Returns:
            BaseLLMProvider instance

        Raises:
            RuntimeError: If no provider available
        """
        preferred = preferred_provider or os.getenv("LLM_PROVIDER", "groq")
        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        provider = None

        if preferred == "groq" and groq_key:
            provider = _try_groq(groq_key)

        elif preferred == "openai" and openai_key:
            provider = _try_openai(openai_key)

        if provider is not None:
            return provider

        # Try fallback if enabled
        if enable_fallback:
            logger.info("Attempting fallback provider...")

            if preferred == "groq" and openai_key:
                provider = _try_openai(openai_key)
            elif preferred == "openai" and groq_key:
                provider = _try_groq(groq_key)

            if provider is not None:
                return provider

        raise RuntimeError(
            "No LLM provider available. "
            "Please set GROQ_API_KEY or OPENAI_API_KEY in .env file.\n"
            "Get free Groq key at: https://console.groq.com/keys"
        )

    @staticmethod
    def get_available_providers() -> list[str]:
        """Return list of configured providers."""
        providers = []
        if os.getenv("GROQ_API_KEY"):
            providers.append("groq")
        if os.getenv("OPENAI_API_KEY"):
            providers.append("openai")
        return providers


def _try_groq(api_key: str) -> Optional[BaseLLMProvider]:
    """Try to create and validate a Groq provider."""
    try:
        from neurosync.llm.groq_provider import GroqProvider

        provider = GroqProvider(api_key=api_key)
        if provider.is_available():
            logger.info("Using Groq provider (FREE)")
            return provider
        logger.warning("Groq configured but unavailable")
    except Exception as e:
        logger.warning("Groq initialization failed: {}", e)
    return None


def _try_openai(api_key: str) -> Optional[BaseLLMProvider]:
    """Try to create and validate an OpenAI provider."""
    try:
        from neurosync.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(api_key=api_key)
        if provider.is_available():
            logger.info("Using OpenAI provider")
            return provider
        logger.warning("OpenAI configured but unavailable")
    except Exception as e:
        logger.warning("OpenAI initialization failed: {}", e)
    return None
