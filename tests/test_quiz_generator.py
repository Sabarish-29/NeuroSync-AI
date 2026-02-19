"""
Tests for quiz generator (Step 7).

Tests GPT-4 quiz question generation, quiz bank, and export.
"""

from __future__ import annotations

import json

import pytest

from neurosync.content.generators.quiz_generator import QuizBank, QuizGenerator, QuizQuestion
from neurosync.content.formats.quiz import QuizExporter, QuizOutput


class TestQuizGenerator:
    """Test quiz generation with mocked OpenAI."""

    @pytest.mark.asyncio
    async def test_generates_quiz(self, quiz_generator, sample_concepts):
        """Creates quiz questions for each concept."""
        result = await quiz_generator.generate_quiz(sample_concepts, "Biology 101")
        assert isinstance(result, QuizBank)
        assert len(result.questions) >= 2  # at least some from each concept
        assert result.total_points > 0

    @pytest.mark.asyncio
    async def test_empty_concepts(self, quiz_generator):
        """Returns empty QuizBank for no concepts."""
        result = await quiz_generator.generate_quiz([], "Empty")
        assert len(result.questions) == 0

    @pytest.mark.asyncio
    async def test_quiz_bank_serialization(self, quiz_generator, sample_concepts):
        """Quiz bank serializes to valid JSON dict."""
        result = await quiz_generator.generate_quiz(sample_concepts, "Bio")
        data = result.to_dict()
        assert "questions" in data
        assert "total_points" in data
        # Round-trip through JSON
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["total_questions"] == len(result.questions)


class TestQuizExporter:
    """Test quiz JSON export."""

    @pytest.mark.asyncio
    async def test_export_json(self, quiz_generator, sample_concepts, tmp_path):
        """Exports quiz bank to JSON file."""
        bank = await quiz_generator.generate_quiz(sample_concepts, "Bio")
        exporter = QuizExporter()
        output = exporter.export(bank, tmp_path / "quiz.json")
        assert isinstance(output, QuizOutput)
        assert output.question_count > 0
        # Verify file content
        data = json.loads((tmp_path / "quiz.json").read_text())
        assert "questions" in data
