"""
Tests for concept extractor (Step 7).

Tests GPT-4 concept extraction with mocked API calls.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from neurosync.content.analyzers.concept_extractor import ConceptExtractor, ConceptMap, ExtractedConcept
from neurosync.content.analyzers.complexity_assessor import ComplexityAssessor, ComplexityReport
from neurosync.content.analyzers.structure_analyzer import StructureAnalyzer

from tests.conftest_content import SAMPLE_CONCEPT_RESPONSE, _make_chat_response


# ── Concept Extractor tests ─────────────────────────────────────────


class TestConceptExtractor:
    """Test concept extraction with mocked OpenAI."""

    @pytest.mark.asyncio
    async def test_extract_concepts(self, concept_extractor):
        """Extracts concepts from text chunks via GPT-4."""
        result = await concept_extractor.extract_from_chunks(
            chunks=["Photosynthesis converts light to energy."],
            title="Biology 101",
        )
        assert isinstance(result, ConceptMap)
        assert len(result.concepts) >= 1
        assert result.concepts[0].name == "Photosynthesis"
        assert result.total_chunks_processed == 1

    @pytest.mark.asyncio
    async def test_extract_deduplicates(self, concept_extractor):
        """Duplicate concept names are filtered out across chunks."""
        result = await concept_extractor.extract_from_chunks(
            chunks=["Photosynthesis intro", "Photosynthesis details"],
            title="Biology",
        )
        names = [c.name.lower() for c in result.concepts]
        assert len(names) == len(set(names)), "Should deduplicate concepts"

    @pytest.mark.asyncio
    async def test_empty_chunks(self, concept_extractor):
        """Returns empty ConceptMap for no chunks."""
        result = await concept_extractor.extract_from_chunks(chunks=[], title="Empty")
        assert len(result.concepts) == 0
        assert result.summary == "No content to analyze."


# ── Complexity Assessor tests ────────────────────────────────────────


class TestComplexityAssessor:
    """Test content complexity assessment."""

    def test_simple_text(self):
        """Short simple sentences score as easy."""
        assessor = ComplexityAssessor()
        result = assessor.assess("The cat sat on the mat. It was a big cat.")
        assert isinstance(result, ComplexityReport)
        assert result.difficulty_label in ("easy", "medium")
        assert result.word_count > 0

    def test_complex_text(self):
        """Technical text with jargon scores higher difficulty."""
        assessor = ComplexityAssessor()
        text = (
            "The algorithm demonstrates convergence properties under "
            "asymptotic conditions. The differential equation exhibits "
            "exponential growth with a logarithmic derivative."
        )
        result = assessor.assess(text)
        assert result.difficulty_label in ("hard", "expert")
        assert result.technical_term_density > 0

    def test_empty_text(self):
        """Empty text returns easy with zero counts."""
        assessor = ComplexityAssessor()
        result = assessor.assess("")
        assert result.difficulty_label == "easy"
        assert result.word_count == 0


# ── Structure Analyzer tests ────────────────────────────────────────


class TestStructureAnalyzer:
    """Test document structure detection."""

    def test_detects_headings(self):
        """Finds section headings in text."""
        analyzer = StructureAnalyzer()
        text = "# Introduction\nSome intro text.\n\n# Methods\nSome methods."
        result = analyzer.analyze(text, "Test Doc")
        assert result.total_sections >= 2
        assert result.title == "Test Doc"

    def test_empty_text(self):
        """Empty text produces single-section structure."""
        analyzer = StructureAnalyzer()
        result = analyzer.analyze("", "Empty")
        assert result.title == "Empty"
        assert result.total_sections == 0
