"""
NeuroSync AI — Google Text-to-Speech provider (FREE).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

from gtts import gTTS
from loguru import logger

from neurosync.tts.base_provider import BaseTTSProvider, TTSResult


class GTTSProvider(BaseTTSProvider):
    """
    Free TTS using gTTS library.

    Requires internet connection.
    """

    def __init__(
        self,
        output_dir: str = "generated_audio",
        language: str = "en",
        slow: bool = False,
    ) -> None:
        super().__init__(output_dir)
        self.language = language
        self.slow = slow
        self.provider_name = "gtts"

    async def generate_audio(
        self,
        text: str,
        output_filename: Optional[str] = None,
        **kwargs: Any,
    ) -> TTSResult:
        """Generate audio using gTTS (FREE)."""
        try:
            if not output_filename:
                output_filename = f"audio_{int(time.time())}.mp3"

            output_path = self.output_dir / output_filename

            logger.info("Generating audio with gTTS (FREE)...")
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            tts.save(str(output_path))

            file_size = output_path.stat().st_size

            # Estimate duration (rough: 150 words/minute)
            word_count = len(text.split())
            estimated_duration = (word_count / 150) * 60

            logger.info(
                "gTTS audio: {} ({:.1f} KB, ~{:.0f}s)",
                output_path.name,
                file_size / 1024,
                estimated_duration,
            )

            return TTSResult(
                audio_path=str(output_path),
                duration_seconds=estimated_duration,
                file_size_bytes=file_size,
                provider="gtts",
            )

        except Exception as e:
            logger.error("gTTS error: {}", e)
            raise

    def is_available(self) -> bool:
        """Check if gTTS is available (requires internet)."""
        try:
            gTTS(text="test", lang=self.language)
            return True
        except Exception:
            return False
