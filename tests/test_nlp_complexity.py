"""
Tests for NLP complexity analyzer (Step 4).
"""

import pytest

from neurosync.nlp.processors.complexity import ComplexityAnalyzer, _count_syllables


class TestComplexityAnalyzer:
    """Tests for the ComplexityAnalyzer processor."""

    def test_simple_text_classified_simple(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("The cat sat on the mat. The dog ran fast.")
        assert result.label == "simple"

    def test_complex_text_classified_hard_or_very_hard(self):
        analyzer = ComplexityAnalyzer()
        text = (
            "The mitochondrial electron transport chain comprises four enzymatic complexes "
            "embedded in the inner mitochondrial membrane, facilitating oxidative phosphorylation "
            "through chemiosmotic coupling of proton gradients across the intermembrane space."
        )
        result = analyzer.analyze(text)
        assert result.label in ("hard", "very_hard")
        assert result.score > 10.0

    def test_empty_text_returns_default(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("")
        assert result.label == "moderate"  # default
        assert result.score == 0.0

    def test_short_text_under_min_words(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("Hi there")
        assert result.label == "simple"
        assert result.word_count == 2

    def test_syllable_counter(self):
        assert _count_syllables("cat") == 1
        assert _count_syllables("photosynthesis") >= 4
        assert _count_syllables("a") == 1

    def test_word_and_sentence_counts(self):
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze("This is one sentence. Here is another sentence.")
        assert result.word_count == 8
        assert result.sentence_count == 2
