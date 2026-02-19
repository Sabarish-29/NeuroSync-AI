"""
NeuroSync AI — Readability Analyzer.

Computes multiple readability metrics and checks against grade-level targets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from neurosync.config.settings import NLP_THRESHOLDS
from neurosync.nlp.processors.complexity import _count_syllables


@dataclass
class ReadabilityResult:
    """Result from readability analysis."""
    flesch_reading_ease: float = 0.0     # 0-100 (higher = easier)
    flesch_kincaid_grade: float = 0.0    # US grade level
    avg_sentence_length: float = 0.0
    avg_syllables_per_word: float = 0.0
    appropriate_for_grade: int = 8       # suggested target grade


class ReadabilityAnalyzer:
    """
    Computes readability metrics for educational content or student text.

    Useful for checking whether content matches the student's reading level.
    """

    def __init__(self) -> None:
        self._grade_thresholds = {
            6: float(NLP_THRESHOLDS["READABILITY_GRADE_6_MAX"]),
            8: float(NLP_THRESHOLDS["READABILITY_GRADE_8_MAX"]),
            10: float(NLP_THRESHOLDS["READABILITY_GRADE_10_MAX"]),
            12: float(NLP_THRESHOLDS["READABILITY_GRADE_12_MAX"]),
        }

    def analyze(self, text: str) -> ReadabilityResult:
        """Compute readability metrics for a piece of text."""
        if not text or not text.strip():
            return ReadabilityResult()

        words = re.findall(r"\b[a-zA-Z]+\b", text)
        word_count = len(words)
        if word_count < 3:
            return ReadabilityResult()

        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if s.strip()]
        sentence_count = max(1, len(sentences))

        syllable_count = sum(_count_syllables(w) for w in words)
        avg_sentence_length = word_count / sentence_count
        avg_syllables = syllable_count / word_count

        # Flesch Reading Ease
        fre = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables
        fre = max(0.0, min(100.0, round(fre, 2)))

        # Flesch-Kincaid Grade Level
        fk_grade = 0.39 * avg_sentence_length + 11.8 * avg_syllables - 15.59
        fk_grade = max(0.0, round(fk_grade, 2))

        # Determine appropriate grade
        appropriate = 12
        for grade in sorted(self._grade_thresholds.keys()):
            if fk_grade <= self._grade_thresholds[grade]:
                appropriate = grade
                break

        return ReadabilityResult(
            flesch_reading_ease=fre,
            flesch_kincaid_grade=fk_grade,
            avg_sentence_length=round(avg_sentence_length, 2),
            avg_syllables_per_word=round(avg_syllables, 2),
            appropriate_for_grade=appropriate,
        )
