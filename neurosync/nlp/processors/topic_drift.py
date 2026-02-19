"""
NeuroSync AI — Topic Drift Detector.

Detects when a student's responses drift away from the expected topic/concept.
Uses simple word-overlap similarity (no heavy embeddings needed).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from neurosync.config.settings import NLP_THRESHOLDS


@dataclass
class TopicDriftResult:
    """Result from topic drift detection."""
    drift_detected: bool = False
    similarity_score: float = 1.0      # 1.0 = on topic, 0.0 = completely off
    current_topic_words: list[str] = field(default_factory=list)


class TopicDriftDetector:
    """
    Detects topic drift by comparing word overlap between recent student text
    and a reference topic (concept keywords or initial context).

    Maintains a sliding window of recent texts for trend detection.
    """

    def __init__(self) -> None:
        self._threshold = float(NLP_THRESHOLDS["TOPIC_DRIFT_THRESHOLD"])
        self._window_size = int(NLP_THRESHOLDS["TOPIC_DRIFT_WINDOW_SIZE"])
        self._recent_texts: list[str] = []

    def check(
        self,
        text: str,
        reference_keywords: list[str] | None = None,
    ) -> TopicDriftResult:
        """
        Check if the given text drifts from the expected topic.

        Parameters
        ----------
        text : str
            The student's current text.
        reference_keywords : list[str], optional
            Expected concept keywords. If None, compares against previous texts.
        """
        if not text or not text.strip():
            return TopicDriftResult()

        text_lower = text.lower()
        text_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_lower))

        # Track recent texts
        self._recent_texts.append(text_lower)
        if len(self._recent_texts) > self._window_size + 1:
            self._recent_texts = self._recent_texts[-(self._window_size + 1):]

        # Compare against reference keywords if provided
        if reference_keywords:
            ref_set = {k.lower() for k in reference_keywords if len(k) >= 3}
            similarity = self._jaccard(text_words, ref_set) if ref_set else 1.0
        elif len(self._recent_texts) >= 2:
            # Compare against previous text
            prev_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", self._recent_texts[-2]))
            similarity = self._jaccard(text_words, prev_words)
        else:
            similarity = 1.0

        drift_detected = similarity < self._threshold

        return TopicDriftResult(
            drift_detected=drift_detected,
            similarity_score=round(similarity, 4),
            current_topic_words=sorted(text_words)[:10],
        )

    @staticmethod
    def _jaccard(set_a: set[str], set_b: set[str]) -> float:
        """Compute Jaccard similarity between two word sets."""
        if not set_a and not set_b:
            return 1.0
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0

    def reset(self) -> None:
        """Clear recent text history."""
        self._recent_texts.clear()
