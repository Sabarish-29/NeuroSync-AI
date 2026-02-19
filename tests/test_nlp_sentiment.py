"""
Tests for NLP sentiment analyzer (Step 4).
"""

import pytest

from neurosync.nlp.processors.sentiment import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Tests for the SentimentAnalyzer processor."""

    def test_positive_text_returns_positive_label(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("I love this! It's wonderful and amazing!")
        assert result.label == "positive"
        assert result.polarity > 0.0

    def test_negative_text_returns_negative_or_frustrated(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("This is terrible and awful. I hate it so much.")
        assert result.label in ("negative", "frustrated")
        assert result.polarity < 0.0

    def test_neutral_text_returns_neutral(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Water is composed of hydrogen and oxygen atoms.")
        assert result.label == "neutral"

    def test_empty_text_returns_default(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("")
        assert result.label == "neutral"
        assert result.polarity == 0.0

    def test_trend_tracking(self):
        analyzer = SentimentAnalyzer()
        # Feed several negative texts
        for _ in range(3):
            analyzer.analyze("This is really bad and terrible.")
        trend = analyzer.get_trend()
        assert trend < 0.0

    def test_reset_clears_history(self):
        analyzer = SentimentAnalyzer()
        analyzer.analyze("Great work!")
        analyzer.reset()
        assert analyzer.get_trend() == 0.0
