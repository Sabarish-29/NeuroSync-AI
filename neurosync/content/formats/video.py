"""
NeuroSync AI — Video Format Handler.

Handles video output: metadata, validation, and file management.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class VideoOutput:
    """Video output descriptor."""
    path: str
    duration_seconds: float
    resolution: tuple[int, int]
    fps: int
    codec: str
    file_size_bytes: int
    segment_count: int

    @property
    def file_size_mb(self) -> float:
        return self.file_size_bytes / (1024 * 1024)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "video/mp4",
            "path": self.path,
            "duration_seconds": self.duration_seconds,
            "resolution": f"{self.resolution[0]}x{self.resolution[1]}",
            "fps": self.fps,
            "codec": self.codec,
            "file_size_mb": round(self.file_size_mb, 2),
            "segment_count": self.segment_count,
        }

    def exists(self) -> bool:
        return Path(self.path).exists()
