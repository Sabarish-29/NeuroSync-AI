"""
NeuroSync AI — Gaze signal tests (6 tests).

All tests use synthetic landmarks — no real camera required.
"""

from __future__ import annotations

import time

import pytest

from neurosync.webcam.signals.gaze import GazeSignal
from tests.conftest_webcam import (
    make_neutral_landmarks,
    make_looking_left_landmarks,
    make_no_face_landmarks,
)


class TestGazeSignal:
    """Tests for the GazeSignal processor."""

    def test_gaze_centered_returns_on_screen(self, mock_landmarks_neutral) -> None:
        """Iris centred in eye → on_screen = True."""
        gaze = GazeSignal()
        result = gaze.process(mock_landmarks_neutral)
        assert result.on_screen is True
        assert result.gaze_direction == "screen"
        assert result.confidence > 0.0

    def test_gaze_far_left_triggers_away(self, mock_landmarks_looking_left) -> None:
        """Iris shifted far left → gaze_direction != screen."""
        gaze = GazeSignal()
        result = gaze.process(mock_landmarks_looking_left)
        assert result.gaze_direction in ("left", "away")
        assert result.confidence > 0.0

    def test_gaze_off_screen_duration_accumulates(self) -> None:
        """Consecutive off-screen frames accumulate duration."""
        gaze = GazeSignal()
        lm = make_looking_left_landmarks()
        # Process several off-screen frames
        for _ in range(5):
            result = gaze.process(lm)
            time.sleep(0.01)
        assert result.off_screen_duration_ms > 0

    def test_gaze_off_screen_trigger_fires_at_threshold(self) -> None:
        """Off-screen for > GAZE_OFF_SCREEN_TRIGGER_MS → triggered = True."""
        gaze = GazeSignal()
        # Manually set the off-screen start in the past
        gaze._off_screen_start = time.time() - 5.0  # 5 seconds ago
        lm = make_looking_left_landmarks()
        result = gaze.process(lm)
        assert result.off_screen_triggered is True
        assert result.off_screen_duration_ms >= 4000

    def test_gaze_rolling_majority_vote(self) -> None:
        """20 on-screen + 10 away → majority on-screen wins smoothing."""
        gaze = GazeSignal()
        neutral = make_neutral_landmarks()
        away = make_looking_left_landmarks()

        # Feed 20 on-screen frames
        for _ in range(20):
            gaze.process(neutral)

        # Feed 10 off-screen frames
        for _ in range(10):
            result = gaze.process(away)

        # Majority should still be on-screen (20/30 = 67%)
        assert result.on_screen is True

    def test_gaze_no_face_returns_gracefully(self, mock_landmarks_no_face) -> None:
        """No face → confidence = 0.0, no crash."""
        gaze = GazeSignal()
        result = gaze.process(mock_landmarks_no_face)
        assert result.confidence == 0.0
        assert result.on_screen is False
        assert result.gaze_direction == "away"
