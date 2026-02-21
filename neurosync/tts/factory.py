"""
NeuroSync AI — Factory for TTS providers with fallback.
"""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger

from neurosync.tts.base_provider import BaseTTSProvider
from neurosync.tts.gtts_provider import GTTSProvider


class TTSProviderFactory:
    """Creates TTS providers with fallback."""

    @staticmethod
    def create_provider(
        preferred_provider: Optional[str] = None,
    ) -> BaseTTSProvider:
        """
        Create TTS provider.

        Priority:
        1. Try preferred (gtts or openai)
        2. Fall back to gtts (always available)
        """
        preferred = preferred_provider or os.getenv("TTS_PROVIDER", "gtts")

        if preferred == "openai":
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                try:
                    # Import inline to avoid hard dependency
                    from neurosync.content.tts.openai_tts import OpenAITTS  # noqa: F401

                    logger.info("OpenAI TTS requested but requires client injection")
                except Exception as e:
                    logger.warning("OpenAI TTS import failed: {}", e)

        # Default to gTTS (FREE)
        logger.info("Using gTTS (FREE)")
        return GTTSProvider()
