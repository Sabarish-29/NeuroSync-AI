"""
Tests for slide generator (Step 7).

Tests slide deck creation and PPTX export.
"""

from __future__ import annotations

import pytest

from neurosync.content.generators.slide_generator import SlideContent, SlideDeck, SlideGenerator


class TestSlideGenerator:
    """Test slide generation from concepts."""

    def test_generates_slides(self, sample_concepts):
        """Creates slides from concept list."""
        gen = SlideGenerator()
        deck = gen.generate(
            sample_concepts,
            title="Biology 101",
            summary="Energy in cells",
            objectives=["Understand photosynthesis"],
        )
        assert isinstance(deck, SlideDeck)
        assert deck.slide_count >= 4  # title + objectives + 2 concepts + summary
        assert deck.title == "Biology 101"

    def test_empty_concepts(self):
        """Generates minimal deck with no concepts."""
        gen = SlideGenerator()
        deck = gen.generate([], title="Empty Course")
        # At least title + summary slides
        assert deck.slide_count >= 2

    def test_export_pptx(self, sample_concepts, tmp_path):
        """Exports valid PPTX file to disk."""
        gen = SlideGenerator()
        deck = gen.generate(sample_concepts, title="Test Export")
        path = gen.export_pptx(deck, tmp_path / "test.pptx")
        assert path.exists()
        assert path.suffix == ".pptx"
        assert path.stat().st_size > 0

    def test_export_pptx_bytes(self, sample_concepts):
        """Exports PPTX to bytes buffer."""
        gen = SlideGenerator()
        deck = gen.generate(sample_concepts, title="Byte Export")
        data = gen.export_pptx_bytes(deck)
        assert isinstance(data, bytes)
        assert len(data) > 0
