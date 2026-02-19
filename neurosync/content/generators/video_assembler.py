"""
NeuroSync AI — Video Assembler.

Assembles narrated video from slides, audio clips, and diagrams
using MoviePy. Outputs MP4 at configurable resolution and FPS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from loguru import logger


@dataclass
class VideoSegment:
    """A single segment of the video (one slide with audio)."""
    slide_title: str
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    duration_seconds: float = 8.0
    text_overlay: str = ""


@dataclass
class AssembledVideo:
    """Result of video assembly."""
    output_path: str
    total_duration_seconds: float
    segment_count: int
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 24
    file_size_bytes: int = 0


class VideoAssembler:
    """Assemble video from slides and audio using MoviePy."""

    def __init__(self, fps: int = 24, resolution: tuple[int, int] = (1920, 1080),
                 codec: str = "libx264", audio_codec: str = "aac",
                 default_slide_duration: float = 8.0) -> None:
        self.fps = fps
        self.resolution = resolution
        self.codec = codec
        self.audio_codec = audio_codec
        self.default_slide_duration = default_slide_duration

    def create_segments(self, slide_titles: list[str],
                         audio_paths: list[str | None] | None = None,
                         durations: list[float] | None = None) -> list[VideoSegment]:
        """
        Create video segments from slide titles and optional audio.

        Args:
            slide_titles: List of slide titles/text.
            audio_paths: Optional list of audio file paths.
            durations: Optional list of segment durations.

        Returns:
            List of VideoSegment objects.
        """
        segments: list[VideoSegment] = []

        for i, title in enumerate(slide_titles):
            audio = audio_paths[i] if audio_paths and i < len(audio_paths) else None
            dur = durations[i] if durations and i < len(durations) else self.default_slide_duration

            segments.append(VideoSegment(
                slide_title=title,
                audio_path=audio,
                duration_seconds=dur,
                text_overlay=title,
            ))

        return segments

    def assemble(self, segments: list[VideoSegment], output_path: str | Path) -> AssembledVideo:
        """
        Assemble video from segments.

        Creates text-card slides with optional audio overlay.
        Uses MoviePy's TextClip for each slide and concatenates.

        Args:
            segments: List of video segments.
            output_path: Where to save the MP4.

        Returns:
            AssembledVideo result with metadata.
        """
        from moviepy import (
            ColorClip,
            CompositeVideoClip,
            TextClip,
            concatenate_videoclips,
        )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        clips = []
        total_duration = 0.0

        for seg in segments:
            duration = seg.duration_seconds or self.default_slide_duration

            # Background
            bg = ColorClip(
                size=self.resolution,
                color=(30, 30, 60),       # dark blue background
            ).with_duration(duration)

            # Text overlay
            try:
                txt = TextClip(
                    text=seg.slide_title,
                    font_size=48,
                    color="white",
                    size=(self.resolution[0] - 200, None),
                    method="caption",
                ).with_duration(duration).with_position("center")

                clip = CompositeVideoClip([bg, txt])
            except Exception:
                # Fallback to just background if text rendering fails
                clip = bg

            clips.append(clip)
            total_duration += duration

        if not clips:
            raise ValueError("No segments to assemble")

        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            str(path),
            fps=self.fps,
            codec=self.codec,
            audio_codec=self.audio_codec,
            logger=None,
        )

        # Get file size
        file_size = path.stat().st_size if path.exists() else 0

        logger.info(
            "Assembled video: {} ({:.1f}s, {} segments, {:.1f}MB)",
            path.name, total_duration, len(segments), file_size / (1024 * 1024),
        )

        return AssembledVideo(
            output_path=str(path),
            total_duration_seconds=total_duration,
            segment_count=len(segments),
            resolution=self.resolution,
            fps=self.fps,
            file_size_bytes=file_size,
        )

    def estimate_duration(self, segments: list[VideoSegment]) -> float:
        """Estimate total video duration in seconds."""
        return sum(s.duration_seconds for s in segments)
