"""
NeuroSync AI — Sentiment Analyzer.

Uses TextBlob for polarity/subjectivity analysis of student text.
Maps sentiment to frustration/confusion/engagement signals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger

from neurosync.config.settings import NLP_THRESHOLDS


@dataclass
class SentimentResult:
    """Result from sentiment analysis."""
    polarity: float = 0.0           # -1.0 to 1.0
    subjectivity: float = 0.0      # 0.0 to 1.0
    label: str = "neutral"          # positive, neutral, negative, frustrated
    confidence: float = 0.0


class SentimentAnalyzer:
    """
    Analyses sentiment in student text using TextBlob.

    Tracks a rolling window of recent sentiments to detect trends.
    """

    def __init__(self) -> None:
        self._window_size = int(NLP_THRESHOLDS["SENTIMENT_WINDOW_SIZE"])
        self._frustration_threshold = float(NLP_THRESHOLDS["SENTIMENT_FRUSTRATION_THRESHOLD"])
        self._confusion_threshold = float(NLP_THRESHOLDS["SENTIMENT_CONFUSION_THRESHOLD"])
        self._positive_threshold = float(NLP_THRESHOLDS["SENTIMENT_POSITIVE_THRESHOLD"])
        self._history: list[float] = []

    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment of a piece of text."""
        if not text or not text.strip():
            return SentimentResult()

        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
        except Exception as exc:
            logger.warning("Sentiment analysis failed: {}", exc)
            return SentimentResult()

        # Track history
        self._history.append(polarity)
        if len(self._history) > self._window_size:
            self._history = self._history[-self._window_size:]

        # Classify
        label = self._classify(polarity)
        confidence = min(1.0, abs(polarity) + 0.3)

        return SentimentResult(
            polarity=round(polarity, 4),
            subjectivity=round(subjectivity, 4),
            label=label,
            confidence=round(confidence, 4),
        )

    def _classify(self, polarity: float) -> str:
        """Map polarity to a sentiment label."""
        if polarity <= self._frustration_threshold:
            return "frustrated"
        elif polarity < self._confusion_threshold:
            return "negative"
        elif polarity >= self._positive_threshold:
            return "positive"
        return "neutral"

    def get_trend(self) -> float:
        """Get average sentiment over the recent window. Returns 0 if empty."""
        if not self._history:
            return 0.0
        return sum(self._history) / len(self._history)

    def reset(self) -> None:
        """Clear sentiment history."""
        self._history.clear()
