"""
NeuroSync AI — Answer Quality Assessor.

Evaluates the quality of student answers based on length, keyword overlap,
and structural indicators.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from neurosync.config.settings import NLP_THRESHOLDS


@dataclass
class AnswerQualityResult:
    """Result from answer quality assessment."""
    quality: str = "moderate"     # low, moderate, good, excellent
    score: float = 0.0           # 0.0 to 1.0
    word_count: int = 0
    length_score: float = 0.0
    overlap_score: float = 0.0


class AnswerQualityAssessor:
    """
    Assesses the quality of a student's answer.

    Scoring dimensions:
    - Length: Is the answer long enough to be meaningful?
    - Keyword overlap: Does the answer contain expected concept keywords?
    - Structure: Does it have explanation markers (because, therefore, etc.)?
    """

    # Explanation markers that indicate deeper understanding
    _EXPLANATION_MARKERS = {
        "because", "therefore", "since", "means", "implies",
        "results", "causes", "leads", "explains", "reason",
        "example", "instance", "specifically", "for example",
    }

    def __init__(self) -> None:
        self._min_length = int(NLP_THRESHOLDS["ANSWER_MIN_LENGTH_CHARS"])
        self._good_length = int(NLP_THRESHOLDS["ANSWER_GOOD_LENGTH_CHARS"])
        self._excellent_length = int(NLP_THRESHOLDS["ANSWER_EXCELLENT_LENGTH_CHARS"])
        self._overlap_good = float(NLP_THRESHOLDS["ANSWER_KEYWORD_OVERLAP_GOOD"])
        self._overlap_excellent = float(NLP_THRESHOLDS["ANSWER_KEYWORD_OVERLAP_EXCELLENT"])

    def assess(
        self,
        answer_text: str,
        expected_keywords: list[str] | None = None,
    ) -> AnswerQualityResult:
        """Assess quality of an answer."""
        if not answer_text or not answer_text.strip():
            return AnswerQualityResult(quality="low", score=0.0)

        text = answer_text.strip()
        char_count = len(text)
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        word_count = len(words)

        # 1. Length score (0 to 0.4)
        if char_count < self._min_length:
            length_score = 0.0
        elif char_count < self._good_length:
            length_score = 0.2
        elif char_count < self._excellent_length:
            length_score = 0.3
        else:
            length_score = 0.4

        # 2. Keyword overlap score (0 to 0.4)
        overlap_score = 0.0
        if expected_keywords:
            expected_set = {k.lower() for k in expected_keywords}
            word_set = set(words)
            if expected_set:
                overlap = len(word_set & expected_set) / len(expected_set)
                overlap_score = min(0.4, overlap * 0.4 / self._overlap_excellent)
        else:
            # No expected keywords — give partial credit for length
            overlap_score = min(0.2, length_score * 0.5)

        # 3. Structure score (0 to 0.2) — explanation markers
        marker_count = sum(1 for w in words if w in self._EXPLANATION_MARKERS)
        structure_score = min(0.2, marker_count * 0.1)

        total_score = round(length_score + overlap_score + structure_score, 4)
        quality = self._classify(total_score)

        return AnswerQualityResult(
            quality=quality,
            score=total_score,
            word_count=word_count,
            length_score=round(length_score, 4),
            overlap_score=round(overlap_score, 4),
        )

    def _classify(self, score: float) -> str:
        """Map score to quality label."""
        if score < 0.25:
            return "low"
        elif score < 0.50:
            return "moderate"
        elif score < 0.75:
            return "good"
        return "excellent"
