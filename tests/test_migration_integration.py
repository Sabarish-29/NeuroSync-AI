"""
NeuroSync AI — Migration integration tests.

Verifies that the migration from OpenAI to Groq/gTTS doesn't break
existing functionality. Tests backward compatibility with mock clients.
"""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from neurosync.config.settings import LLM_CONFIG, TTS_CONFIG
from neurosync.content.pipeline import ContentPipeline, PipelineConfig
from neurosync.interventions.generator import InterventionGenerator


# ── Test: Settings include new config ───────────────────────────────


class TestMigrationConfig:
    """Test that new configuration sections exist."""

    def test_llm_config_exists(self) -> None:
        assert "PROVIDER" in LLM_CONFIG
        assert "GROQ_API_KEY" in LLM_CONFIG
        assert "GROQ_MODEL" in LLM_CONFIG
        assert "OPENAI_API_KEY" in LLM_CONFIG
        assert "OPENAI_MODEL" in LLM_CONFIG

    def test_tts_config_exists(self) -> None:
        assert "PROVIDER" in TTS_CONFIG
        assert "LANGUAGE" in TTS_CONFIG
        assert "VOICE_SPEED" in TTS_CONFIG

    def test_llm_config_defaults(self) -> None:
        assert LLM_CONFIG["GROQ_MODEL"] == "llama-3.3-70b-versatile"
        assert LLM_CONFIG["OPENAI_MODEL"] == "gpt-4o"

    def test_tts_config_defaults(self) -> None:
        assert TTS_CONFIG["LANGUAGE"] == "en"
        assert TTS_CONFIG["VOICE_SPEED"] == "normal"


# ── Test: InterventionGenerator backward compatibility ──────────────


class TestInterventionGeneratorCompatibility:
    """Test that InterventionGenerator still works with mocked clients."""

    def test_init_with_api_key(self) -> None:
        """Backward compatible: passing api_key still works."""
        gen = InterventionGenerator(api_key="sk-test-dummy")
        assert gen._api_key == "sk-test-dummy"
        assert gen._model == "gpt-4-turbo-preview"

    def test_init_with_api_key_and_model(self) -> None:
        gen = InterventionGenerator(api_key="sk-test", model="gpt-3.5-turbo")
        assert gen._model == "gpt-3.5-turbo"

    def test_init_uses_groq_when_configured(self) -> None:
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "gsk_test",
        }):
            gen = InterventionGenerator()
            assert gen._llm_provider_type == "groq"
            assert gen._api_key == "gsk_test"
            assert "llama" in gen._model

    def test_init_falls_back_to_openai(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"}
        env["LLM_PROVIDER"] = "openai"
        env["OPENAI_API_KEY"] = "sk-fallback"
        with patch.dict(os.environ, env, clear=True):
            gen = InterventionGenerator()
            assert gen._llm_provider_type == "openai"

    @pytest.mark.asyncio
    async def test_generate_with_mocked_client(self, tmp_path) -> None:
        """Critical: mocked client path still works (all existing tests use this)."""
        from neurosync.interventions.cache.manager import CacheManager
        from neurosync.interventions.cost_tracker import CostTracker

        gen = InterventionGenerator(
            api_key="sk-test-dummy",
            cache_manager=CacheManager(db_path=str(tmp_path / "test.db"), max_size=100),
            cost_tracker=CostTracker(),
        )

        # Mock the client (same pattern as existing tests)
        mock_msg = MagicMock()
        mock_msg.content = "Test response"

        mock_choice = MagicMock()
        mock_choice.message = mock_msg

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150

        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_resp.usage = mock_usage

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        gen._client = mock_client

        result = await gen.generate("explain", {
            "original_content": "Test content",
            "student_grade": 8,
            "student_answer": "I don't know",
            "correct_answer": "Mitochondria",
            "prerequisites": "Basic biology",
        })

        assert result is not None
        assert result.content == "Test response"
        assert result.tokens_used == 150
        assert result.from_cache is False


# ── Test: ContentPipeline backward compatibility ────────────────────


class TestContentPipelineCompatibility:
    """Test that ContentPipeline still works with injected clients."""

    def test_pipeline_accepts_openai_client(self) -> None:
        """Backward compatible: passing openai_client still works."""
        mock_client = MagicMock()
        pipeline = ContentPipeline(openai_client=mock_client)
        assert pipeline.client is mock_client

    def test_pipeline_creates_client_when_none(self) -> None:
        """When no client provided, factory tries env vars."""
        env = {k: v for k, v in os.environ.items()
               if k not in ("GROQ_API_KEY", "OPENAI_API_KEY")}
        with patch.dict(os.environ, env, clear=True):
            pipeline = ContentPipeline()
            # No API keys -> client is None (graceful degradation)
            assert pipeline.client is None

    def test_pipeline_creates_groq_client(self) -> None:
        """When Groq configured, pipeline creates Groq-compatible client."""
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "gsk_test",
        }):
            pipeline = ContentPipeline()
            # Client should be created (AsyncOpenAI pointed at Groq)
            assert pipeline.client is not None


# ── Test: Provider abstraction layer ────────────────────────────────


class TestProviderAbstraction:
    """Test that the provider abstraction layer works standalone."""

    def test_groq_provider_init(self) -> None:
        from neurosync.llm.groq_provider import GroqProvider

        provider = GroqProvider(api_key="fake")
        assert provider.provider_name == "groq"
        assert provider.model == "llama-3.3-70b-versatile"

    def test_openai_provider_init(self) -> None:
        from neurosync.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider(api_key="fake")
        assert provider.provider_name == "openai"
        assert provider.model == "gpt-4o"

    def test_gtts_provider_init(self, tmp_path) -> None:
        from neurosync.tts.gtts_provider import GTTSProvider

        provider = GTTSProvider(output_dir=str(tmp_path))
        assert provider.provider_name == "gtts"
        assert provider.language == "en"

    def test_factory_available_providers(self) -> None:
        from neurosync.llm.factory import LLMProviderFactory

        providers = LLMProviderFactory.get_available_providers()
        assert isinstance(providers, list)

    def test_tts_factory_creates_gtts(self) -> None:
        from neurosync.tts.factory import TTSProviderFactory
        from neurosync.tts.gtts_provider import GTTSProvider

        provider = TTSProviderFactory.create_provider()
        assert isinstance(provider, GTTSProvider)
