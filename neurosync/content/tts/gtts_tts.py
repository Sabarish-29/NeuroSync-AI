"""
NeuroSync AI — gTTS-based TTS integration (FREE).

Drop-in replacement for OpenAITTS, using gTTS instead of the OpenAI
speech API. Exposes the same interface so ContentPipeline is unaffected.

Cost: $0.00
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Optional

from gtts import gTTS
from loguru import logger

from neurosync.content.tts.openai_tts import AudioSegment


class GttsTTS:
    """
    Generate audio narration using gTTS (Google Text-to-Speech, FREE).

    Matches the interface of OpenAITTS so it can be swapped in without
    changing the rest of ContentPipeline.
    """

    def __init__(self, language: str = "en", slow: bool = False) -> None:
        self.language = language
        self.slow = slow
        logger.info("GttsTTS initialized (FREE, language={})", language)

    async def generate_audio(
        self,
        text: str,
        concept_name: str = "",
        output_dir: str | Path | None = None,
    ) -> AudioSegment:
        """
        Generate audio from text using gTTS.

        Args:
            text: Text to speak.
            concept_name: Label for the segment.
            output_dir: If provided, saves the MP3 there.

        Returns:
            AudioSegment with audio bytes and optional file path.
        """
        if not text.strip():
            return AudioSegment(concept_name=concept_name, text=text)

        audio_path: Optional[str] = None
        audio_bytes: Optional[bytes] = None

        tts_obj = gTTS(text=text, lang=self.language, slow=self.slow)

        if output_dir:
            dir_path = Path(output_dir)
            dir_path.mkdir(parents=True, exist_ok=True)
            safe_name = concept_name.replace(" ", "_").lower()[:50] or "audio"
            audio_path = str(dir_path / f"{safe_name}.mp3")
            tts_obj.save(audio_path)
            audio_bytes = Path(audio_path).read_bytes()
        else:
            # No output dir: write to a temp file, read bytes, then delete
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            tts_obj.save(tmp_path)
            audio_bytes = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)

        # Estimate duration (~2.5 words per second at normal speed)
        word_count = len(text.split())
        estimated_duration = word_count / 2.5

        logger.info(
            "Generated gTTS audio: {} ({} words, ~{:.1f}s, FREE)",
            concept_name, word_count, estimated_duration,
        )

        return AudioSegment(
            concept_name=concept_name,
            text=text,
            audio_path=audio_path,
            audio_bytes=audio_bytes,
            duration_seconds=estimated_duration,
        )

    async def generate_for_scripts(
        self,
        scripts: list[Any],
        output_dir: str | Path | None = None,
    ) -> list[AudioSegment]:
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
                logger.warning("gTTS failed for {}: {}", script.concept_name, e)
                segments.append(AudioSegment(
                    concept_name=script.concept_name,
                    text=script.script_text,
                ))

        logger.info("Generated {} audio segments (gTTS, FREE)", len(segments))
        return segments
