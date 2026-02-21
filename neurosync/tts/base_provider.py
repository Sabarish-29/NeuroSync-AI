"""
NeuroSync AI — Abstract base class for TTS providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel


class TTSResult(BaseModel):
    """Standardized TTS result."""

    audio_path: str
    duration_seconds: float
    file_size_bytes: int
    provider: str


class BaseTTSProvider(ABC):
    """Base class for all TTS providers."""

    def __init__(self, output_dir: str = "generated_audio") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.provider_name = "base"

    @abstractmethod
    async def generate_audio(
        self,
        text: str,
        output_filename: Optional[str] = None,
        **kwargs: Any,
    ) -> TTSResult:
        """Generate audio from text."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
