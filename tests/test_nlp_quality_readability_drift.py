"""
Tests for NLP answer quality, readability, and topic drift (Step 4).
"""

import pytest

from neurosync.nlp.processors.answer_quality import AnswerQualityAssessor
from neurosync.nlp.processors.readability import ReadabilityAnalyzer
from neurosync.nlp.processors.topic_drift import TopicDriftDetector


class TestAnswerQualityAssessor:
    """Tests for the AnswerQualityAssessor processor."""

    def test_short_answer_low_quality(self):
        assessor = AnswerQualityAssessor()
        result = assessor.assess("yes")
        assert result.quality == "low"
        assert result.score < 0.25

    def test_detailed_answer_good_quality(self):
        assessor = AnswerQualityAssessor()
        result = assessor.assess(
            "Photosynthesis is the process by which plants convert light energy "
            "from the sun into chemical energy stored in glucose. This occurs in "
            "the chloroplasts, because the thylakoid membranes contain chlorophyll "
            "which absorbs light energy.",
            expected_keywords=["photosynthesis", "light", "energy", "glucose", "chloroplast"],
        )
        assert result.quality in ("good", "excellent")
        assert result.score >= 0.50

    def test_empty_answer_low_quality(self):
        assessor = AnswerQualityAssessor()
        result = assessor.assess("")
        assert result.quality == "low"
        assert result.score == 0.0


class TestReadabilityAnalyzer:
    """Tests for the ReadabilityAnalyzer processor."""

    def test_simple_text_reading_ease(self):
        analyzer = ReadabilityAnalyzer()
        result = analyzer.analyze("The cat sat on the mat. The dog ran and played.")
        assert result.flesch_reading_ease > 50.0  # Should be easy
        assert result.appropriate_for_grade <= 8

    def test_complex_text_lower_reading_ease(self):
        analyzer = ReadabilityAnalyzer()
        result = analyzer.analyze(
            "The mitochondrial electron transport chain comprises four enzymatic complexes "
            "embedded in the inner mitochondrial membrane, facilitating oxidative phosphorylation "
            "through chemiosmotic coupling of proton gradients."
        )
        assert result.flesch_kincaid_grade > 8.0

    def test_empty_text_returns_default(self):
        analyzer = ReadabilityAnalyzer()
        result = analyzer.analyze("")
        assert result.flesch_reading_ease == 0.0


class TestTopicDriftDetector:
    """Tests for the TopicDriftDetector processor."""

    def test_on_topic_no_drift(self):
        detector = TopicDriftDetector()
        result = detector.check(
            "Photosynthesis uses light energy to produce glucose.",
            reference_keywords=["photosynthesis", "light", "energy", "glucose"],
        )
        assert not result.drift_detected
        assert result.similarity_score > 0.0

    def test_off_topic_detects_drift(self):
        detector = TopicDriftDetector()
        result = detector.check(
            "My favorite movie is about space exploration and astronauts.",
            reference_keywords=["photosynthesis", "light", "energy", "glucose"],
        )
        assert result.drift_detected
        assert result.similarity_score < 0.40

    def test_empty_text_no_drift(self):
        detector = TopicDriftDetector()
        result = detector.check("")
        assert not result.drift_detected

    def test_reset_clears_state(self):
        detector = TopicDriftDetector()
        detector.check("Some text about science.")
        detector.reset()
        # After reset, no previous texts to compare
        result = detector.check("New text.")
        assert result.similarity_score == 1.0
