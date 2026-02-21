"""
NeuroSync AI — Tests for LLM provider abstraction layer.

Tests both Groq and OpenAI providers, the factory, and interface compatibility.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from neurosync.llm.base_provider import BaseLLMProvider, LLMMessage, LLMResponse
from neurosync.llm.groq_provider import GroqProvider
from neurosync.llm.openai_provider import OpenAIProvider
from neurosync.llm.factory import LLMProviderFactory


# ── Unit Tests: LLMMessage / LLMResponse models ────────────────────


class TestLLMModels:
    """Test Pydantic data models."""

    def test_llm_message_creation(self) -> None:
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_llm_response_creation(self) -> None:
        resp = LLMResponse(
            content="Answer",
            tokens_used=42,
            model="test-model",
            provider="test",
            finish_reason="stop",
        )
        assert resp.content == "Answer"
        assert resp.tokens_used == 42
        assert resp.provider == "test"
        assert resp.finish_reason == "stop"

    def test_llm_message_roles(self) -> None:
        for role in ("system", "user", "assistant"):
            msg = LLMMessage(role=role, content="test")
            assert msg.role == role


# ── Unit Tests: GroqProvider ────────────────────────────────────────


class TestGroqProvider:
    """Test Groq provider without real API calls."""

    def test_provider_name(self) -> None:
        provider = GroqProvider(api_key="fake-key")
        assert provider.provider_name == "groq"
        assert provider.get_provider_name() == "groq"

    def test_default_model(self) -> None:
        provider = GroqProvider(api_key="fake-key")
        assert provider.model == "llama-3.3-70b-versatile"

    def test_custom_model(self) -> None:
        provider = GroqProvider(api_key="fake-key", model="llama-3.1-8b-instant")
        assert provider.model == "llama-3.1-8b-instant"

    def test_rate_limit_tracking(self) -> None:
        provider = GroqProvider(api_key="fake-key")
        assert provider.requests_per_minute == 30
        assert len(provider.request_timestamps) == 0

    def test_chat_completion_with_mock(self) -> None:
        """Test chat completion with a mocked Groq client."""
        provider = GroqProvider(api_key="fake-key")

        # Mock the internal client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "4"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 15

        provider.client = MagicMock()
        provider.client.chat.completions.create.return_value = mock_response

        messages = [LLMMessage(role="user", content="What is 2+2?")]
        response = provider.chat_completion(messages, max_tokens=10)

        assert response.content == "4"
        assert response.provider == "groq"
        assert response.tokens_used == 15
        assert response.finish_reason == "stop"

    def test_is_available_returns_false_on_error(self) -> None:
        provider = GroqProvider(api_key="fake-key")
        provider.client = MagicMock()
        provider.client.chat.completions.create.side_effect = Exception("API error")
        assert provider.is_available() is False


# ── Unit Tests: OpenAIProvider ──────────────────────────────────────


class TestOpenAIProvider:
    """Test OpenAI provider without real API calls."""

    def test_provider_name(self) -> None:
        provider = OpenAIProvider(api_key="fake-key")
        assert provider.provider_name == "openai"
        assert provider.get_provider_name() == "openai"

    def test_default_model(self) -> None:
        provider = OpenAIProvider(api_key="fake-key")
        assert provider.model == "gpt-4o"

    def test_custom_model(self) -> None:
        provider = OpenAIProvider(api_key="fake-key", model="gpt-3.5-turbo")
        assert provider.model == "gpt-3.5-turbo"

    def test_chat_completion_with_mock(self) -> None:
        """Test chat completion with a mocked OpenAI client."""
        provider = OpenAIProvider(api_key="fake-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "4"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 20

        provider.client = MagicMock()
        provider.client.chat.completions.create.return_value = mock_response

        messages = [LLMMessage(role="user", content="What is 2+2?")]
        response = provider.chat_completion(messages, max_tokens=10)

        assert response.content == "4"
        assert response.provider == "openai"
        assert response.tokens_used == 20
        assert response.finish_reason == "stop"

    def test_is_available_returns_false_on_error(self) -> None:
        provider = OpenAIProvider(api_key="fake-key")
        provider.client = MagicMock()
        provider.client.chat.completions.create.side_effect = Exception("API error")
        assert provider.is_available() is False


# ── Unit Tests: Interface Compatibility ─────────────────────────────


class TestInterfaceCompatibility:
    """Ensure both providers have identical interfaces."""

    def test_both_providers_are_base_subclasses(self) -> None:
        groq = GroqProvider(api_key="fake")
        openai = OpenAIProvider(api_key="fake")
        assert isinstance(groq, BaseLLMProvider)
        assert isinstance(openai, BaseLLMProvider)

    def test_both_have_required_methods(self) -> None:
        for cls in (GroqProvider, OpenAIProvider):
            provider = cls(api_key="fake")
            assert hasattr(provider, "chat_completion")
            assert hasattr(provider, "is_available")
            assert hasattr(provider, "get_provider_name")
            assert callable(provider.chat_completion)
            assert callable(provider.is_available)
            assert callable(provider.get_provider_name)

    def test_both_return_llm_response(self) -> None:
        """Both providers return LLMResponse from chat_completion."""
        for cls in (GroqProvider, OpenAIProvider):
            provider = cls(api_key="fake")

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "test"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage.total_tokens = 10

            provider.client = MagicMock()
            provider.client.chat.completions.create.return_value = mock_response

            messages = [LLMMessage(role="user", content="test")]
            response = provider.chat_completion(messages, max_tokens=5)
            assert isinstance(response, LLMResponse)


# ── Unit Tests: LLMProviderFactory ──────────────────────────────────


class TestLLMProviderFactory:
    """Test the factory pattern for provider creation."""

    def test_get_available_providers_empty(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            providers = LLMProviderFactory.get_available_providers()
            assert "groq" not in providers
            assert "openai" not in providers

    def test_get_available_providers_with_groq(self) -> None:
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=False):
            providers = LLMProviderFactory.get_available_providers()
            assert "groq" in providers

    def test_get_available_providers_with_openai(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False):
            providers = LLMProviderFactory.get_available_providers()
            assert "openai" in providers

    def test_factory_raises_when_no_providers(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            # Remove all API keys
            env = {k: v for k, v in os.environ.items()
                   if k not in ("GROQ_API_KEY", "OPENAI_API_KEY")}
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(RuntimeError, match="No LLM provider available"):
                    LLMProviderFactory.create_provider(enable_fallback=False)


# ── Integration Tests (require API keys) ────────────────────────────


@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="No Groq key configured",
)
class TestGroqIntegration:
    """Integration tests that require a real Groq API key."""

    def test_groq_chat_completion(self) -> None:
        provider = GroqProvider(api_key=os.environ["GROQ_API_KEY"])
        messages = [
            LLMMessage(role="user", content="What is 2+2? Answer with just the number."),
        ]
        response = provider.chat_completion(messages, max_tokens=10)
        assert response.provider == "groq"
        assert response.tokens_used > 0
        assert "4" in response.content

    def test_groq_is_available(self) -> None:
        provider = GroqProvider(api_key=os.environ["GROQ_API_KEY"])
        assert provider.is_available() is True


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="No OpenAI key configured",
)
class TestOpenAIIntegration:
    """Integration tests that require a real OpenAI API key."""

    def test_openai_chat_completion(self) -> None:
        provider = OpenAIProvider(api_key=os.environ["OPENAI_API_KEY"])
        messages = [
            LLMMessage(role="user", content="What is 2+2? Answer with just the number."),
        ]
        response = provider.chat_completion(messages, max_tokens=10)
        assert response.provider == "openai"
        assert response.tokens_used > 0
        assert "4" in response.content

    def test_openai_is_available(self) -> None:
        provider = OpenAIProvider(api_key=os.environ["OPENAI_API_KEY"])
        assert provider.is_available() is True
