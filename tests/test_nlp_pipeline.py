"""
Tests for NLP pipeline orchestrator and integration (Step 4).
"""

import pytest

from neurosync.core.events import NLPResult, TextEvent
from neurosync.nlp.pipeline import NLPPipeline


class TestNLPPipeline:
    """Tests for the NLPPipeline orchestrator."""

    def test_pipeline_returns_nlp_result(self, nlp_pipeline: NLPPipeline):
        result = nlp_pipeline.analyze("Photosynthesis converts light to energy.")
        assert isinstance(result, NLPResult)
        assert result.word_count > 0
        assert result.sentiment_label in ("positive", "neutral", "negative", "frustrated")
        assert result.complexity_label in ("simple", "moderate", "hard", "very_hard")

    def test_pipeline_tracks_text_count(self, nlp_pipeline: NLPPipeline):
        assert nlp_pipeline.text_count == 0
        nlp_pipeline.analyze("First text.")
        nlp_pipeline.analyze("Second text about science.")
        assert nlp_pipeline.text_count == 2

    def test_pipeline_empty_text(self, nlp_pipeline: NLPPipeline):
        result = nlp_pipeline.analyze("")
        assert result.word_count == 0
        assert result.sentiment_label == "neutral"
        assert nlp_pipeline.text_count == 0  # empty doesn't count

    def test_pipeline_with_expected_keywords(self, nlp_pipeline: NLPPipeline):
        result = nlp_pipeline.analyze(
            "Photosynthesis uses light energy in the chloroplasts to create glucose.",
            expected_keywords=["photosynthesis", "light", "energy", "glucose", "chloroplast"],
        )
        assert result.answer_quality in ("moderate", "good", "excellent")

    def test_pipeline_analyze_event(self, nlp_pipeline: NLPPipeline, text_event: TextEvent):
        result = nlp_pipeline.analyze_event(text_event)
        assert isinstance(result, NLPResult)
        assert result.text == text_event.text

    def test_pipeline_reset(self, nlp_pipeline: NLPPipeline):
        nlp_pipeline.analyze("Some text to analyze.")
        assert nlp_pipeline.text_count == 1
        nlp_pipeline.reset()
        assert nlp_pipeline.text_count == 0

    def test_pipeline_get_trends(self, nlp_pipeline: NLPPipeline):
        nlp_pipeline.analyze("I love this topic!")
        trends = nlp_pipeline.get_trends()
        assert "sentiment_trend" in trends
        assert "confusion_trend" in trends

    def test_pipeline_accessor_properties(self, nlp_pipeline: NLPPipeline):
        """Verify all sub-processor accessors work."""
        assert nlp_pipeline.sentiment_analyzer is not None
        assert nlp_pipeline.complexity_analyzer is not None
        assert nlp_pipeline.keyword_extractor is not None
        assert nlp_pipeline.answer_quality_assessor is not None
        assert nlp_pipeline.confusion_detector is not None
        assert nlp_pipeline.readability_analyzer is not None
        assert nlp_pipeline.topic_drift_detector is not None
