"""
NeuroSync AI — Tests for TTS provider abstraction layer.

Tests gTTS provider, factory, and base interface.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from neurosync.tts.base_provider import BaseTTSProvider, TTSResult
from neurosync.tts.gtts_provider import GTTSProvider
from neurosync.tts.factory import TTSProviderFactory


# ── Unit Tests: TTSResult model ─────────────────────────────────────


class TestTTSResult:
    """Test the Pydantic TTS result model."""

    def test_tts_result_creation(self) -> None:
        result = TTSResult(
            audio_path="/tmp/test.mp3",
            duration_seconds=10.5,
            file_size_bytes=1024,
            provider="gtts",
        )
        assert result.audio_path == "/tmp/test.mp3"
        assert result.duration_seconds == 10.5
        assert result.file_size_bytes == 1024
        assert result.provider == "gtts"


# ── Unit Tests: GTTSProvider ────────────────────────────────────────


class TestGTTSProvider:
    """Test gTTS provider without real network calls."""

    def test_provider_name(self, tmp_path: Path) -> None:
        provider = GTTSProvider(output_dir=str(tmp_path))
        assert provider.provider_name == "gtts"

    def test_default_language(self, tmp_path: Path) -> None:
        provider = GTTSProvider(output_dir=str(tmp_path))
        assert provider.language == "en"

    def test_custom_language(self, tmp_path: Path) -> None:
        provider = GTTSProvider(output_dir=str(tmp_path), language="es")
        assert provider.language == "es"

    def test_output_dir_creation(self, tmp_path: Path) -> None:
        out = tmp_path / "new_dir"
        provider = GTTSProvider(output_dir=str(out))
        assert out.exists()

    def test_is_subclass_of_base(self, tmp_path: Path) -> None:
        provider = GTTSProvider(output_dir=str(tmp_path))
        assert isinstance(provider, BaseTTSProvider)


# ── Unit Tests: TTSProviderFactory ──────────────────────────────────


class TestTTSProviderFactory:
    """Test the TTS factory."""

    def test_factory_creates_gtts_by_default(self) -> None:
        provider = TTSProviderFactory.create_provider()
        assert isinstance(provider, GTTSProvider)

    def test_factory_with_gtts_preference(self) -> None:
        provider = TTSProviderFactory.create_provider(preferred_provider="gtts")
        assert isinstance(provider, GTTSProvider)

    def test_factory_with_env_var(self) -> None:
        with patch.dict(os.environ, {"TTS_PROVIDER": "gtts"}):
            provider = TTSProviderFactory.create_provider()
            assert isinstance(provider, GTTSProvider)

    def test_factory_falls_back_to_gtts_when_openai_unavailable(self) -> None:
        """If OpenAI TTS requested but no key, fall back to gTTS."""
        with patch.dict(os.environ, {"TTS_PROVIDER": "openai"}, clear=False):
            env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
            with patch.dict(os.environ, env, clear=True):
                provider = TTSProviderFactory.create_provider()
                assert isinstance(provider, GTTSProvider)


# ── Integration Tests (require network) ─────────────────────────────


class TestGTTSIntegration:
    """Integration tests for gTTS (requires internet)."""

    @pytest.mark.asyncio
    async def test_generate_audio(self, tmp_path: Path) -> None:
        provider = GTTSProvider(output_dir=str(tmp_path))
        result = await provider.generate_audio(
            text="This is a test.",
            output_filename="test_gtts.mp3",
        )

        assert result.provider == "gtts"
        assert Path(result.audio_path).exists()
        assert result.file_size_bytes > 0
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_generate_audio_auto_filename(self, tmp_path: Path) -> None:
        provider = GTTSProvider(output_dir=str(tmp_path))
        result = await provider.generate_audio(text="Hello world.")

        assert result.provider == "gtts"
        assert Path(result.audio_path).exists()

    def test_is_available(self, tmp_path: Path) -> None:
        provider = GTTSProvider(output_dir=str(tmp_path))
        # gTTS should be available if internet is accessible
        available = provider.is_available()
        assert isinstance(available, bool)
