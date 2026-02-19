"""
NeuroSync AI — OpenAI TTS Integration.

Generates narration audio from scripts using OpenAI's text-to-speech API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from loguru import logger


@dataclass
class AudioSegment:
    """A generated audio segment."""
    concept_name: str
    text: str
    audio_path: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    duration_seconds: float = 0.0


class OpenAITTS:
    """Generate audio narration using OpenAI TTS API."""

    def __init__(self, client: Any = None, model: str = "tts-1",
                 voice: str = "alloy", speed: float = 1.0) -> None:
        self.client = client
        self.model = model
        self.voice = voice
        self.speed = speed

    async def generate_audio(self, text: str, concept_name: str = "",
                              output_dir: str | Path | None = None) -> AudioSegment:
        """
        Generate audio from text.

        Args:
            text: Text to speak.
            concept_name: Name for the segment.
            output_dir: Directory to save audio file.

        Returns:
            AudioSegment with audio bytes/path.
        """
        if self.client is None:
            raise RuntimeError("OpenAI client not configured")

        if not text.strip():
            return AudioSegment(concept_name=concept_name, text=text)

        response = await self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            speed=self.speed,
        )

        audio_bytes = response.content
        audio_path = None

        if output_dir:
            dir_path = Path(output_dir)
            dir_path.mkdir(parents=True, exist_ok=True)
            safe_name = concept_name.replace(" ", "_").lower()[:50] or "audio"
            audio_path = str(dir_path / f"{safe_name}.mp3")
            Path(audio_path).write_bytes(audio_bytes)

        # Estimate duration (~150 words/min at 1.0 speed)
        word_count = len(text.split())
        estimated_duration = (word_count / 2.5) / self.speed

        logger.info(
            "Generated TTS audio: {} ({} words, ~{:.1f}s)",
            concept_name, word_count, estimated_duration,
        )

        return AudioSegment(
            concept_name=concept_name,
            text=text,
            audio_path=audio_path,
            audio_bytes=audio_bytes,
            duration_seconds=estimated_duration,
        )

    async def generate_for_scripts(self, scripts: list[Any],
                                     output_dir: str | Path | None = None) -> list[AudioSegment]:
        """
        Generate audio for all scripts.

        Args:
            scripts: List of NarrationScript objects.
            output_dir: Directory to save audio files.

        Returns:
            List of AudioSegment objects.
        """
        segments: list[AudioSegment] = []

        for script in scripts:
            try:
                seg = await self.generate_audio(
                    text=script.script_text,
                    concept_name=script.concept_name,
                    output_dir=output_dir,
                )
                segments.append(seg)
            except Exception as e:
                logger.warning("TTS failed for {}: {}", script.concept_name, e)
                segments.append(AudioSegment(
                    concept_name=script.concept_name,
                    text=script.script_text,
                ))

        logger.info("Generated {} audio segments", len(segments))
        return segments
