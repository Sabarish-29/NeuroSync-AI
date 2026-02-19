"""
NeuroSync AI — Retention predictor.

Uses a fitted forgetting curve to predict future retention and
compute the optimal review timestamp.
"""

from __future__ import annotations

import math

from neurosync.config.settings import SPACED_REPETITION_CONFIG as CFG
from neurosync.spaced_repetition.forgetting_curve.models import (
    FittedCurve,
    ReviewSchedule,
)


class RetentionPredictor:
    """Predicts future retention and finds the optimal review time."""

    def __init__(self, review_threshold: float | None = None) -> None:
        self.review_threshold: float = float(
            review_threshold or CFG["REVIEW_THRESHOLD"]
        )

    # ------------------------------------------------------------------
    def predict_retention(
        self,
        curve: FittedCurve,
        hours_from_mastery: float,
    ) -> float:
        """Return predicted retention (0-1) at *hours_from_mastery*."""
        days = hours_from_mastery / 24.0
        retention = curve.r0 * math.exp(-days / curve.tau_days)
        return max(0.0, min(1.0, retention))

    # ------------------------------------------------------------------
    def find_review_time(
        self,
        curve: FittedCurve,
        mastery_timestamp: float,
    ) -> ReviewSchedule:
        """
        Compute the optimal review timestamp.

        Solves R(t) = threshold for *t* and subtracts a safety buffer so
        the student is quizzed just **before** they forget.
        """
        if curve.r0 <= self.review_threshold:
            days_until_threshold = 0.0
        else:
            days_until_threshold = -curve.tau_days * math.log(
                self.review_threshold / curve.r0
            )

        buffer = float(CFG["SAFETY_BUFFER_DAYS"])
        days_until_review = max(0.0, days_until_threshold - buffer)

        review_timestamp = mastery_timestamp + (days_until_review * 24 * 3600)
        predicted_retention = self.predict_retention(curve, days_until_review * 24)

        return ReviewSchedule(
            review_at_timestamp=review_timestamp,
            days_from_mastery=days_until_review,
            predicted_retention_at_review=predicted_retention,
            curve_confidence=curve.confidence,
        )
