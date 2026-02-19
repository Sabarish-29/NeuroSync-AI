"""
NeuroSync AI — Difficulty adapter for spaced-repetition quizzes.

Adjusts quiz difficulty based on the review number and recent
performance trajectory.
"""

from __future__ import annotations


class DifficultyAdapter:
    """Maps review-number + recent score to a difficulty label."""

    LEVELS = ("easy", "medium", "hard")

    def determine_difficulty(
        self,
        review_number: int,
        recent_score: float | None = None,
    ) -> str:
        """
        Return ``"easy"`` / ``"medium"`` / ``"hard"`` for the next review.

        * Review 1 (2 h after mastery) → easy
        * Review 2 (≈24 h) → medium
        * Review 3+ → hard (unless score dropped below 60 → medium)
        """
        if review_number <= 1:
            return "easy"
        if review_number == 2:
            return "medium"
        # review_number >= 3
        if recent_score is not None and recent_score < 60:
            return "medium"
        return "hard"
