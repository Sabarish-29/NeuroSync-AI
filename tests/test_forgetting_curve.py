"""
Step 8 — Forgetting-curve tests (6 tests).
"""

from __future__ import annotations

import math

import pytest

from neurosync.spaced_repetition.forgetting_curve.fitter import ForgettingCurveFitter
from neurosync.spaced_repetition.forgetting_curve.models import (
    FittedCurve,
    RetentionPoint,
)
from neurosync.spaced_repetition.forgetting_curve.predictor import RetentionPredictor


class TestForgettingCurveFitter:

    def test_fit_exponential_curve_with_4_points(
        self, fitter: ForgettingCurveFitter, sample_retention_4pts: list[RetentionPoint],
    ):
        """4 data points → valid exponential fit."""
        curve = fitter.fit_curve(sample_retention_4pts)
        assert curve.model == "exponential"
        assert curve.data_points == 4
        assert curve.fitted_params is not None

    def test_fit_returns_default_with_insufficient_data(
        self, fitter: ForgettingCurveFitter, sample_retention_2pts: list[RetentionPoint],
    ):
        """< 3 points → default curve."""
        curve = fitter.fit_curve(sample_retention_2pts)
        assert curve.model == "default"
        assert curve.confidence == 0.0

    def test_fitted_tau_reasonable_range(
        self, fitter: ForgettingCurveFitter, sample_retention_4pts: list[RetentionPoint],
    ):
        """Fitted τ should be 0.1-30 days."""
        curve = fitter.fit_curve(sample_retention_4pts)
        assert 0.1 <= curve.tau_days <= 30.0

    def test_curve_confidence_calculated(
        self, fitter: ForgettingCurveFitter, sample_retention_4pts: list[RetentionPoint],
    ):
        """R² should be > 0 for well-behaved data."""
        curve = fitter.fit_curve(sample_retention_4pts)
        assert curve.confidence > 0.0


class TestRetentionPredictor:

    def test_predict_retention_at_future_time(self, predictor: RetentionPredictor, fitted_curve: FittedCurve):
        """Retention drops over time."""
        r_now = predictor.predict_retention(fitted_curve, hours_from_mastery=0)
        r_later = predictor.predict_retention(fitted_curve, hours_from_mastery=120)
        assert r_now > r_later
        assert 0.0 <= r_later <= 1.0

    def test_find_review_time_before_threshold(self, predictor: RetentionPredictor, fitted_curve: FittedCurve):
        """Review should be scheduled before retention drops to 70 %."""
        import time
        mastery_ts = time.time()
        schedule = predictor.find_review_time(fitted_curve, mastery_ts)
        assert schedule.review_at_timestamp >= mastery_ts
        assert schedule.predicted_retention_at_review >= predictor.review_threshold
