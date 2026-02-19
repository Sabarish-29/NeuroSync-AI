"""
NeuroSync AI — Slides Format Handler.

Handles PPTX slide deck output.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SlidesOutput:
    """Slide deck output descriptor."""
    path: str
    slide_count: int
    title: str
    file_size_bytes: int = 0

    @property
    def file_size_mb(self) -> float:
        return self.file_size_bytes / (1024 * 1024)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "application/pptx",
            "path": self.path,
            "slide_count": self.slide_count,
            "title": self.title,
            "file_size_mb": round(self.file_size_mb, 2),
        }

    def exists(self) -> bool:
        return Path(self.path).exists()
