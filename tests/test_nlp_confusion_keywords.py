"""
Tests for NLP confusion detector and keyword extractor (Step 4).
"""

import pytest

from neurosync.nlp.processors.confusion import ConfusionDetector
from neurosync.nlp.processors.keywords import KeywordExtractor


class TestConfusionDetector:
    """Tests for the ConfusionDetector processor."""

    def test_confused_text_scores_high(self):
        detector = ConfusionDetector()
        result = detector.detect(
            "I'm not sure what this means? Maybe I don't understand? "
            "I guess I'm confused about the whole concept."
        )
        assert result.score > 0.3
        assert result.label in ("moderate", "high")
        assert result.hedge_count > 0
        assert result.question_count >= 2

    def test_clear_text_scores_low(self):
        detector = ConfusionDetector()
        result = detector.detect(
            "Photosynthesis converts carbon dioxide and water into glucose and oxygen."
        )
        assert result.score < 0.15
        assert result.label == "none"

    def test_empty_text_returns_default(self):
        detector = ConfusionDetector()
        result = detector.detect("")
        assert result.score == 0.0
        assert result.label == "none"

    def test_trend_tracking(self):
        detector = ConfusionDetector()
        detector.detect("Maybe I don't know? I'm confused perhaps?")
        detector.detect("I'm really not sure? Possibly wrong?")
        trend = detector.get_trend()
        assert trend > 0.0

    def test_reset_clears_history(self):
        detector = ConfusionDetector()
        detector.detect("I'm confused?")
        detector.reset()
        assert detector.get_trend() == 0.0


class TestKeywordExtractor:
    """Tests for the KeywordExtractor processor."""

    def test_extracts_keywords_from_text(self):
        extractor = KeywordExtractor()
        result = extractor.extract(
            "Photosynthesis is the process by which plants convert light energy "
            "into chemical energy. Photosynthesis occurs in the chloroplasts."
        )
        assert len(result.keywords) > 0
        assert "photosynthesis" in result.keywords

    def test_empty_text_returns_empty(self):
        extractor = KeywordExtractor()
        result = extractor.extract("")
        assert result.keywords == []
        assert result.keyword_count == 0

    def test_keyword_overlap_computation(self):
        extractor = KeywordExtractor()
        extracted = ["photosynthesis", "light", "energy", "water"]
        expected = ["photosynthesis", "light", "energy", "glucose"]
        overlap = extractor.compute_overlap(extracted, expected)
        assert overlap == 0.75  # 3 out of 4

    def test_keyword_overlap_with_empty_expected(self):
        extractor = KeywordExtractor()
        overlap = extractor.compute_overlap(["photosynthesis"], [])
        assert overlap == 0.0
