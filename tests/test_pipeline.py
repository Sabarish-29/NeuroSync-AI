"""
Tests for content generation pipeline (Step 7).

Tests the pipeline orchestrator, progress tracking, markdown export,
story export, and TTS integration — all with mocked APIs.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from neurosync.content.formats.markdown import MarkdownGenerator, MarkdownOutput
from neurosync.content.formats.story import StoryExporter, StoryOutput
from neurosync.content.generators.story_generator import FullStory, StorySegment
from neurosync.content.progress_tracker import PipelineStage, ProgressTracker
from neurosync.content.tts.openai_tts import AudioSegment, OpenAITTS

from tests.conftest_content import _make_tts_response


# ── Progress Tracker tests ──────────────────────────────────────────


class TestProgressTracker:
    """Test pipeline progress tracking."""

    def test_stage_lifecycle(self):
        """Stages progress through pending → running → completed."""
        tracker = ProgressTracker()
        tracker.start_pipeline()
        tracker.start_stage(PipelineStage.PARSING, "Reading PDF")

        progress = tracker.progress
        assert progress.current_stage == PipelineStage.PARSING
        stage = progress.stages[PipelineStage.PARSING.value]
        assert stage.status == "running"

        tracker.complete_stage(PipelineStage.PARSING, "Done")
        assert progress.stages[PipelineStage.PARSING.value].status == "completed"
        assert progress.stages[PipelineStage.PARSING.value].progress_pct == 100.0

    def test_overall_progress(self):
        """Overall progress increases as stages complete."""
        tracker = ProgressTracker()
        tracker.start_pipeline()
        assert tracker.progress.overall_progress_pct == 0.0

        tracker.start_stage(PipelineStage.PARSING)
        tracker.complete_stage(PipelineStage.PARSING)
        assert tracker.progress.overall_progress_pct > 0.0

    def test_failure_tracking(self):
        """Failed stages record error messages."""
        tracker = ProgressTracker()
        tracker.start_pipeline()
        tracker.start_stage(PipelineStage.PARSING)
        tracker.fail_stage(PipelineStage.PARSING, "File corrupt")

        assert tracker.progress.stages[PipelineStage.PARSING.value].status == "failed"
        assert tracker.progress.stages[PipelineStage.PARSING.value].error == "File corrupt"

    def test_callback_fires(self):
        """Progress callback is invoked on updates."""
        calls = []
        tracker = ProgressTracker(callback=lambda p: calls.append(p))
        tracker.start_pipeline()
        tracker.start_stage(PipelineStage.PARSING)
        assert len(calls) >= 2  # start_pipeline + start_stage


# ── Markdown Export tests ───────────────────────────────────────────


class TestMarkdownGenerator:
    """Test Markdown notes generation."""

    def test_generates_markdown(self, sample_concepts):
        """Produces valid Markdown from concepts."""
        gen = MarkdownGenerator()
        md = gen.generate(
            sample_concepts,
            title="Biology 101",
            summary="Energy in cells",
            objectives=["Understand photosynthesis"],
        )
        assert "# Biology 101" in md
        assert "## Key Concepts" in md
        assert "Photosynthesis" in md

    def test_export_file(self, sample_concepts, tmp_path):
        """Exports Markdown to file and returns descriptor."""
        gen = MarkdownGenerator()
        content = gen.generate(sample_concepts, "Test")
        output = gen.export(content, tmp_path / "notes.md")
        assert isinstance(output, MarkdownOutput)
        assert output.word_count > 0
        assert (tmp_path / "notes.md").exists()


# ── Story Export tests ──────────────────────────────────────────────


class TestStoryExporter:
    """Test story Markdown export."""

    def test_export_story(self, tmp_path):
        """Exports FullStory to Markdown file."""
        story = FullStory(
            title="Test Story",
            introduction="Once upon a time...",
            segments=[
                StorySegment(
                    concept_name="Concept A",
                    story_text="A story about concept A.",
                    analogy="A is like X.",
                    moral="Understanding A matters.",
                ),
            ],
            conclusion="The end.",
        )
        exporter = StoryExporter()
        output = exporter.export(story, tmp_path / "story.md")
        assert isinstance(output, StoryOutput)
        assert output.segment_count == 1
        assert (tmp_path / "story.md").exists()
        content = (tmp_path / "story.md").read_text()
        assert "Test Story" in content


# ── TTS tests ──────────────────────────────────────────────────────


class TestOpenAITTS:
    """Test TTS with mocked OpenAI speech API."""

    @pytest.mark.asyncio
    async def test_generate_audio(self, tts_engine):
        """Generates audio bytes from text."""
        result = await tts_engine.generate_audio(
            text="Hello world", concept_name="Greeting",
        )
        assert isinstance(result, AudioSegment)
        assert result.audio_bytes == b"fake-audio-mp3-content"
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_generate_audio_to_file(self, tts_engine, tmp_path):
        """Saves audio to file when output_dir is specified."""
        result = await tts_engine.generate_audio(
            text="Hello world",
            concept_name="test_audio",
            output_dir=tmp_path,
        )
        assert result.audio_path is not None
        from pathlib import Path
        assert Path(result.audio_path).exists()
