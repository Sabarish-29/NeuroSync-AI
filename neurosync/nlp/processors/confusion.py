"""
NeuroSync AI — Confusion Detector.

Detects confusion/uncertainty in student text by looking for hedge words,
question marks, negation patterns, and vague language.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from neurosync.config.settings import NLP_THRESHOLDS


# Hedge words indicate uncertainty
_HEDGE_WORDS: set[str] = {
    "maybe", "perhaps", "possibly", "probably", "might", "could",
    "unsure", "confused", "confusing", "unclear", "uncertain",
    "guess", "think", "suppose", "assume", "wonder",
    "not sure", "don't know", "no idea", "hard to understand",
    "don't understand", "doesn't make sense", "lost", "stuck",
    "idk", "dunno", "kinda", "sorta", "somewhat", "roughly",
}

# Negation words amplify confusion signal
_NEGATION_WORDS: set[str] = {
    "not", "no", "never", "neither", "nobody", "nothing",
    "nowhere", "nor", "don't", "doesn't", "didn't", "won't",
    "wouldn't", "couldn't", "shouldn't", "can't", "cannot",
    "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
}


@dataclass
class ConfusionResult:
    """Result from confusion detection."""
    score: float = 0.0        # 0.0 to 1.0
    label: str = "none"       # none, mild, moderate, high
    hedge_count: int = 0
    question_count: int = 0
    negation_count: int = 0


class ConfusionDetector:
    """
    Detects confusion and uncertainty in student text.

    Scores are based on weighted counts of hedge words, question marks,
    and negations. Capped at 1.0.
    """

    def __init__(self) -> None:
        self._hedge_weight = float(NLP_THRESHOLDS["CONFUSION_HEDGE_WEIGHT"])
        self._question_weight = float(NLP_THRESHOLDS["CONFUSION_QUESTION_WEIGHT"])
        self._negation_weight = float(NLP_THRESHOLDS["CONFUSION_NEGATION_WEIGHT"])
        self._threshold = float(NLP_THRESHOLDS["CONFUSION_THRESHOLD"])
        self._history: list[float] = []

    def detect(self, text: str) -> ConfusionResult:
        """Detect confusion level in text."""
        if not text or not text.strip():
            return ConfusionResult()

        text_lower = text.lower()
        words = re.findall(r"\b[a-zA-Z']+\b", text_lower)

        # Count hedge words (check multi-word phrases first)
        hedge_count = 0
        for phrase in _HEDGE_WORDS:
            if " " in phrase:
                hedge_count += text_lower.count(phrase)
            elif phrase in words:
                hedge_count += words.count(phrase)

        # Count question marks
        question_count = text.count("?")

        # Count negations
        negation_count = sum(1 for w in words if w in _NEGATION_WORDS)

        # Compute weighted score
        raw_score = (
            hedge_count * self._hedge_weight
            + question_count * self._question_weight
            + negation_count * self._negation_weight
        )
        score = min(1.0, round(raw_score, 4))

        # Track history
        self._history.append(score)
        if len(self._history) > 10:
            self._history = self._history[-10:]

        label = self._classify(score)

        return ConfusionResult(
            score=score,
            label=label,
            hedge_count=hedge_count,
            question_count=question_count,
            negation_count=negation_count,
        )

    def _classify(self, score: float) -> str:
        """Map score to confusion label."""
        if score < 0.15:
            return "none"
        elif score < 0.35:
            return "mild"
        elif score < self._threshold:
            return "moderate"
        return "high"

    def get_trend(self) -> float:
        """Get average confusion over recent history."""
        if not self._history:
            return 0.0
        return sum(self._history) / len(self._history)

    def reset(self) -> None:
        """Clear history."""
        self._history.clear()
