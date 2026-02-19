"""
Tests for video assembler (Step 7).

Tests segment creation and video assembly (mocked MoviePy).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from neurosync.content.generators.video_assembler import AssembledVideo, VideoAssembler, VideoSegment


class TestVideoAssembler:
    """Test video assembly logic."""

    def test_create_segments(self):
        """Creates segments from slide titles."""
        asm = VideoAssembler()
        segments = asm.create_segments(
            slide_titles=["Intro", "Concept 1", "Concept 2", "Summary"],
            durations=[5.0, 8.0, 8.0, 5.0],
        )
        assert len(segments) == 4
        assert segments[0].slide_title == "Intro"
        assert segments[0].duration_seconds == 5.0

    def test_create_segments_defaults(self):
        """Uses default duration when not specified."""
        asm = VideoAssembler(default_slide_duration=10.0)
        segments = asm.create_segments(["Slide 1", "Slide 2"])
        assert len(segments) == 2
        assert segments[0].duration_seconds == 10.0

    def test_estimate_duration(self):
        """Calculates total duration from segments."""
        asm = VideoAssembler()
        segments = [
            VideoSegment(slide_title="A", duration_seconds=5.0),
            VideoSegment(slide_title="B", duration_seconds=10.0),
        ]
        assert asm.estimate_duration(segments) == 15.0

    def test_assemble_empty_raises(self):
        """Empty segments raise ValueError."""
        asm = VideoAssembler()
        with pytest.raises(ValueError, match="No segments"):
            asm.assemble([], "output.mp4")
