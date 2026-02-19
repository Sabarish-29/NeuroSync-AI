"""
NeuroSync AI — NLP Pipeline Orchestrator (Step 4).

Coordinates all NLP processors into a single analysis pass. Takes raw text
and returns an NLPResult with sentiment, complexity, confusion, keywords,
answer quality, readability, and topic drift.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from neurosync.core.events import NLPResult, TextEvent
from neurosync.nlp.processors.answer_quality import AnswerQualityAssessor
from neurosync.nlp.processors.complexity import ComplexityAnalyzer
from neurosync.nlp.processors.confusion import ConfusionDetector
from neurosync.nlp.processors.keywords import KeywordExtractor
from neurosync.nlp.processors.readability import ReadabilityAnalyzer
from neurosync.nlp.processors.sentiment import SentimentAnalyzer
from neurosync.nlp.processors.topic_drift import TopicDriftDetector


class NLPPipeline:
    """
    Orchestrates all NLP processors to produce a unified NLPResult.

    Usage::

        pipeline = NLPPipeline()
        result = pipeline.analyze("I think photosynthesis converts light to energy")
        print(result.sentiment_label, result.complexity_label)
    """

    def __init__(self) -> None:
        self._sentiment = SentimentAnalyzer()
        self._complexity = ComplexityAnalyzer()
        self._keywords = KeywordExtractor()
        self._answer_quality = AnswerQualityAssessor()
        self._confusion = ConfusionDetector()
        self._readability = ReadabilityAnalyzer()
        self._topic_drift = TopicDriftDetector()
        self._text_count = 0
        logger.info("NLPPipeline initialised")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        text: str,
        expected_keywords: list[str] | None = None,
        reference_keywords: list[str] | None = None,
    ) -> NLPResult:
        """
        Run all NLP processors on a piece of text.

        Parameters
        ----------
        text : str
            The student text to analyze.
        expected_keywords : list[str], optional
            Expected concept keywords (for answer quality overlap scoring).
        reference_keywords : list[str], optional
            Topic reference keywords (for topic drift detection).

        Returns
        -------
        NLPResult
            Aggregated NLP analysis result.
        """
        if not text or not text.strip():
            return NLPResult(text=text or "")

        self._text_count += 1

        # Run all processors
        sentiment = self._sentiment.analyze(text)
        complexity = self._complexity.analyze(text)
        kw = self._keywords.extract(text)
        answer_q = self._answer_quality.assess(text, expected_keywords)
        confusion = self._confusion.detect(text)
        drift = self._topic_drift.check(text, reference_keywords)

        result = NLPResult(
            text=text,
            sentiment_polarity=sentiment.polarity,
            sentiment_subjectivity=sentiment.subjectivity,
            sentiment_label=sentiment.label,
            complexity_score=complexity.score,
            complexity_label=complexity.label,
            confusion_score=confusion.score,
            confusion_label=confusion.label,
            answer_quality=answer_q.quality,
            answer_quality_score=answer_q.score,
            keywords=kw.keywords,
            topic_drift_detected=drift.drift_detected,
            word_count=complexity.word_count,
        )

        logger.debug(
            "NLP analysis #{}: sentiment={}, complexity={}, confusion={}, quality={}",
            self._text_count,
            sentiment.label,
            complexity.label,
            confusion.label,
            answer_q.quality,
        )

        return result

    def analyze_event(
        self,
        event: TextEvent,
        expected_keywords: list[str] | None = None,
        reference_keywords: list[str] | None = None,
    ) -> NLPResult:
        """
        Convenience method to analyze a TextEvent directly.
        """
        return self.analyze(
            text=event.text,
            expected_keywords=expected_keywords,
            reference_keywords=reference_keywords,
        )

    # ------------------------------------------------------------------
    # Accessor properties
    # ------------------------------------------------------------------

    @property
    def sentiment_analyzer(self) -> SentimentAnalyzer:
        return self._sentiment

    @property
    def complexity_analyzer(self) -> ComplexityAnalyzer:
        return self._complexity

    @property
    def keyword_extractor(self) -> KeywordExtractor:
        return self._keywords

    @property
    def answer_quality_assessor(self) -> AnswerQualityAssessor:
        return self._answer_quality

    @property
    def confusion_detector(self) -> ConfusionDetector:
        return self._confusion

    @property
    def readability_analyzer(self) -> ReadabilityAnalyzer:
        return self._readability

    @property
    def topic_drift_detector(self) -> TopicDriftDetector:
        return self._topic_drift

    @property
    def text_count(self) -> int:
        """Number of texts analyzed since creation."""
        return self._text_count

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all processor states."""
        self._sentiment.reset()
        self._confusion.reset()
        self._topic_drift.reset()
        self._text_count = 0
        logger.info("NLPPipeline reset")

    def get_trends(self) -> dict[str, float]:
        """Get current trend scores from stateful processors."""
        return {
            "sentiment_trend": self._sentiment.get_trend(),
            "confusion_trend": self._confusion.get_trend(),
        }
