"""
Tests for script generator (Step 7).

Tests GPT-4 narration script generation with mocked API.
"""

from __future__ import annotations

import pytest

from neurosync.content.generators.script_generator import FullScript, NarrationScript, ScriptGenerator


class TestScriptGenerator:
    """Test script generation with mocked OpenAI."""

    @pytest.mark.asyncio
    async def test_generates_scripts(self, script_generator, sample_concepts):
        """Creates narration scripts for each concept."""
        result = await script_generator.generate_scripts(sample_concepts, "Biology 101")
        assert isinstance(result, FullScript)
        # intro + 2 concepts + outro = 4
        assert len(result.scripts) >= 4
        assert result.total_word_count > 0
        assert result.total_duration_seconds > 0

    @pytest.mark.asyncio
    async def test_empty_concepts(self, script_generator):
        """Returns empty FullScript for no concepts."""
        result = await script_generator.generate_scripts([], "Empty")
        assert len(result.scripts) == 0

    @pytest.mark.asyncio
    async def test_script_word_count(self, script_generator, sample_concepts):
        """Each script has non-zero word count."""
        result = await script_generator.generate_scripts(sample_concepts, "Bio")
        for script in result.scripts:
            assert isinstance(script, NarrationScript)
            assert script.word_count > 0
