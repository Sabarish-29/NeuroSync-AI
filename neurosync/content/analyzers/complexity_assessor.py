"""
NeuroSync AI — Complexity Assessor.

Assesses the difficulty level of content to drive adaptive
generation of slides, narration speed, and quiz difficulty.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass


@dataclass
class ComplexityReport:
    """Content complexity assessment result."""
    flesch_kincaid_grade: float
    flesch_reading_ease: float
    avg_sentence_length: float
    avg_word_length: float
    technical_term_density: float
    difficulty_label: str                # easy, medium, hard, expert
    recommended_audience: str            # e.g., "high school", "undergraduate"
    word_count: int
    sentence_count: int

    @property
    def numeric_difficulty(self) -> float:
        """Return 0.0 – 1.0 difficulty score."""
        labels = {"easy": 0.2, "medium": 0.5, "hard": 0.75, "expert": 0.95}
        return labels.get(self.difficulty_label, 0.5)


# Common technical/academic terms that boost perceived complexity
TECHNICAL_INDICATORS = {
    "algorithm", "theorem", "hypothesis", "coefficient", "derivative",
    "integral", "polynomial", "equation", "function", "variable",
    "parameter", "matrix", "vector", "tensor", "eigenvalue",
    "regression", "correlation", "probability", "distribution",
    "convergence", "divergence", "asymptotic", "logarithmic",
    "exponential", "differential", "calculus", "topology",
    "morphism", "isomorphism", "homeomorphism", "manifold",
    "quantum", "entropy", "nucleotide", "peptide", "enzyme",
    "catalyst", "oxidation", "mitochondria", "chromosome",
    "photosynthesis", "thermodynamics", "electromagnetic",
}


class ComplexityAssessor:
    """Assess content complexity for adaptive generation."""

    def assess(self, text: str) -> ComplexityReport:
        """
        Analyze text complexity using readability metrics.

        Args:
            text: The text to analyze.

        Returns:
            ComplexityReport with readability scores and difficulty label.
        """
        if not text or not text.strip():
            return ComplexityReport(
                flesch_kincaid_grade=0.0,
                flesch_reading_ease=100.0,
                avg_sentence_length=0.0,
                avg_word_length=0.0,
                technical_term_density=0.0,
                difficulty_label="easy",
                recommended_audience="general",
                word_count=0,
                sentence_count=0,
            )

        sentences = self._split_sentences(text)
        words = self._split_words(text)
        sentence_count = max(len(sentences), 1)
        word_count = len(words)

        if word_count == 0:
            return ComplexityReport(
                flesch_kincaid_grade=0.0,
                flesch_reading_ease=100.0,
                avg_sentence_length=0.0,
                avg_word_length=0.0,
                technical_term_density=0.0,
                difficulty_label="easy",
                recommended_audience="general",
                word_count=0,
                sentence_count=sentence_count,
            )

        syllable_count = sum(self._count_syllables(w) for w in words)
        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count
        avg_word_length = sum(len(w) for w in words) / word_count

        # Flesch-Kincaid Grade Level
        fk_grade = (
            0.39 * avg_sentence_length
            + 11.8 * avg_syllables_per_word
            - 15.59
        )
        fk_grade = max(0.0, round(fk_grade, 1))

        # Flesch Reading Ease
        fre = (
            206.835
            - 1.015 * avg_sentence_length
            - 84.6 * avg_syllables_per_word
        )
        fre = max(0.0, min(100.0, round(fre, 1)))

        # Technical term density
        lower_words = {w.lower() for w in words}
        tech_count = len(lower_words & TECHNICAL_INDICATORS)
        tech_density = tech_count / max(word_count, 1)

        # Determine difficulty label
        difficulty = self._classify_difficulty(fk_grade, tech_density)
        audience = self._recommend_audience(fk_grade)

        return ComplexityReport(
            flesch_kincaid_grade=fk_grade,
            flesch_reading_ease=fre,
            avg_sentence_length=round(avg_sentence_length, 1),
            avg_word_length=round(avg_word_length, 1),
            technical_term_density=round(tech_density, 4),
            difficulty_label=difficulty,
            recommended_audience=audience,
            word_count=word_count,
            sentence_count=sentence_count,
        )

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        parts = re.split(r"[.!?]+", text)
        return [s.strip() for s in parts if s.strip()]

    def _split_words(self, text: str) -> list[str]:
        """Split text into words."""
        return re.findall(r"[a-zA-Z]+", text)

    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word."""
        word = word.lower().strip()
        if len(word) <= 2:
            return 1
        # Remove trailing e
        if word.endswith("e"):
            word = word[:-1]
        vowels = "aeiou"
        count = 0
        prev_vowel = False
        for ch in word:
            is_vowel = ch in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        return max(count, 1)

    def _classify_difficulty(self, grade: float, tech_density: float) -> str:
        """Classify content difficulty."""
        if grade <= 6.0 and tech_density < 0.01:
            return "easy"
        elif grade <= 10.0 and tech_density < 0.03:
            return "medium"
        elif grade <= 14.0 or tech_density < 0.05:
            return "hard"
        return "expert"

    def _recommend_audience(self, grade: float) -> str:
        """Recommend appropriate audience level."""
        if grade <= 6.0:
            return "middle school"
        elif grade <= 8.0:
            return "high school"
        elif grade <= 12.0:
            return "undergraduate"
        return "graduate/professional"
