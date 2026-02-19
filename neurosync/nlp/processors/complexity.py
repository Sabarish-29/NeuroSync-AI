"""
NeuroSync AI — Text Complexity Analyzer.

Computes Flesch-Kincaid grade level and classifies text difficulty.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from neurosync.config.settings import NLP_THRESHOLDS


@dataclass
class ComplexityResult:
    """Result from complexity analysis."""
    score: float = 0.0        # Flesch-Kincaid grade level
    label: str = "moderate"   # simple, moderate, hard, very_hard
    word_count: int = 0
    sentence_count: int = 0
    syllable_count: int = 0


def _count_syllables(word: str) -> int:
    """Estimate syllable count for an English word."""
    word = word.lower().strip()
    if len(word) <= 2:
        return 1
    # Remove trailing silent-e
    if word.endswith("e"):
        word = word[:-1]
    # Count vowel groups
    count = len(re.findall(r"[aeiouy]+", word))
    return max(1, count)


class ComplexityAnalyzer:
    """
    Computes Flesch-Kincaid grade level for student text.

    Uses syllable counting + sentence/word ratios for a grade-level estimate.
    """

    def __init__(self) -> None:
        self._simple_threshold = float(NLP_THRESHOLDS["COMPLEXITY_SIMPLE_THRESHOLD"])
        self._moderate_threshold = float(NLP_THRESHOLDS["COMPLEXITY_MODERATE_THRESHOLD"])
        self._hard_threshold = float(NLP_THRESHOLDS["COMPLEXITY_HARD_THRESHOLD"])
        self._min_words = int(NLP_THRESHOLDS["COMPLEXITY_WORD_COUNT_MIN"])

    def analyze(self, text: str) -> ComplexityResult:
        """Analyze complexity of a piece of text."""
        if not text or not text.strip():
            return ComplexityResult()

        words = re.findall(r"\b[a-zA-Z]+\b", text)
        word_count = len(words)
        if word_count < self._min_words:
            return ComplexityResult(word_count=word_count, label="simple")

        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if s.strip()]
        sentence_count = max(1, len(sentences))

        syllable_count = sum(_count_syllables(w) for w in words)

        # Flesch-Kincaid Grade Level
        fk_grade = (
            0.39 * (word_count / sentence_count)
            + 11.8 * (syllable_count / word_count)
            - 15.59
        )
        fk_grade = max(0.0, round(fk_grade, 2))

        label = self._classify(fk_grade)

        return ComplexityResult(
            score=fk_grade,
            label=label,
            word_count=word_count,
            sentence_count=sentence_count,
            syllable_count=syllable_count,
        )

    def _classify(self, grade: float) -> str:
        """Map grade level to a complexity label."""
        if grade < self._simple_threshold:
            return "simple"
        elif grade < self._moderate_threshold:
            return "moderate"
        elif grade < self._hard_threshold:
            return "hard"
        return "very_hard"
