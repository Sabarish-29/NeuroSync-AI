"""
NeuroSync AI — Expression signal tests (5 tests).

All tests use synthetic landmarks — no real camera required.
"""

from __future__ import annotations

import pytest
import numpy as np

from neurosync.webcam.signals.expression import ExpressionSignal
from neurosync.webcam.mediapipe_processor import RawLandmarks
from tests.conftest_webcam import (
    make_neutral_landmarks,
    make_frustrated_landmarks,
    make_bored_landmarks,
    _default_landmarks,
)


class TestExpressionSignal:
    """Tests for the ExpressionSignal processor."""

    def test_neutral_expression_low_scores(self, mock_landmarks_neutral) -> None:
        """Normal distances → all expression scores < 0.3."""
        expr = ExpressionSignal()
        result = expr.process(mock_landmarks_neutral)
        assert result.frustration_tension < 0.35
        assert result.confusion_indicator < 0.35

    def test_brow_furrow_raises_frustration(self, mock_landmarks_frustrated) -> None:
        """Decreased inner brow distance → frustration_tension elevated."""
        expr = ExpressionSignal()
        result = expr.process(mock_landmarks_frustrated)
        assert result.frustration_tension > 0.20

    def test_jaw_drop_raises_boredom(self, mock_landmarks_bored) -> None:
        """Increased lip gap + jaw drop → boredom_indicator elevated."""
        expr = ExpressionSignal()
        result = expr.process(mock_landmarks_bored)
        assert result.boredom_indicator > 0.3

    def test_ema_smoothing_prevents_spikes(self) -> None:
        """Single frustrated frame amidst neutrals → smoothed score stays low."""
        expr = ExpressionSignal()
        neutral = make_neutral_landmarks()
        frustrated = make_frustrated_landmarks()

        # Process 10 neutral frames first
        for _ in range(10):
            expr.process_and_mark_initialised(neutral)

        # Single spike
        spike_result = expr.process(frustrated)

        # The EMA should dampen the spike — frustration should stay below
        # the raw frustrated value
        assert spike_result.frustration_tension < 0.8

        # Process more neutrals — should decrease
        for _ in range(5):
            result = expr.process(neutral)
        assert result.frustration_tension < spike_result.frustration_tension

    def test_expression_face_width_normalised(self) -> None:
        """Same expression at different face sizes → similar scores."""
        expr1 = ExpressionSignal()
        expr2 = ExpressionSignal()

        lm_normal = _default_landmarks()
        # Scale face up by 1.5x (all coords shifted toward edges)
        lm_large = [(x * 1.0, y * 1.0, z) for x, y, z in lm_normal]  # same for normalised

        r1 = expr1.process(RawLandmarks(
            face_landmarks=lm_normal, face_detected=True,
            frame_width=640, frame_height=480,
        ))
        r2 = expr2.process(RawLandmarks(
            face_landmarks=lm_large, face_detected=True,
            frame_width=640, frame_height=480,
        ))

        # Scores should be very close (same normalised landmarks)
        assert abs(r1.frustration_tension - r2.frustration_tension) < 0.15
        assert abs(r1.boredom_indicator - r2.boredom_indicator) < 0.15
