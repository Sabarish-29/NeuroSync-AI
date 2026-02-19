"""
Tests for story generator (Step 7).

Tests GPT-4 story-based explanation generation.
"""

from __future__ import annotations

import pytest

from neurosync.content.generators.story_generator import FullStory, StoryGenerator, StorySegment


class TestStoryGenerator:
    """Test story generation with mocked OpenAI."""

    @pytest.mark.asyncio
    async def test_generates_story(self, story_generator, sample_concepts):
        """Creates story segments for each concept."""
        result = await story_generator.generate_story(sample_concepts, "Biology 101")
        assert isinstance(result, FullStory)
        assert len(result.segments) == 2  # one per concept
        assert result.introduction != ""
        assert result.conclusion != ""
        assert result.total_word_count > 0

    @pytest.mark.asyncio
    async def test_empty_concepts(self, story_generator):
        """Returns empty FullStory for no concepts."""
        result = await story_generator.generate_story([], "Empty")
        assert len(result.segments) == 0

    @pytest.mark.asyncio
    async def test_story_has_analogy(self, story_generator, sample_concepts):
        """Each story segment includes an analogy."""
        result = await story_generator.generate_story(sample_concepts, "Bio")
        for seg in result.segments:
            assert isinstance(seg, StorySegment)
            assert seg.analogy != ""
