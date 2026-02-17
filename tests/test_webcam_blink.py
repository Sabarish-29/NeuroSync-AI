"""
NeuroSync AI — Blink signal tests (5 tests).

All tests use synthetic landmarks — no real camera required.
"""

from __future__ import annotations

import time

import pytest

from neurosync.webcam.signals.blink import BlinkSignal
from tests.conftest_webcam import (
    make_neutral_landmarks,
    make_closed_eyes_landmarks,
)


class TestBlinkSignal:
    """Tests for the BlinkSignal processor."""

    def test_ear_low_detects_blink(self) -> None:
        """EAR < 0.20 → blink counted after re-opening."""
        blink = BlinkSignal()
        neutral = make_neutral_landmarks()
        closed = make_closed_eyes_landmarks()

        # Open → closed (3 frames) → open = 1 blink
        blink.process(neutral)
        blink.process(closed)
        blink.process(closed)
        blink.process(closed)
        result = blink.process(neutral)

        # At least one blink should be registered
        assert len(blink._blink_times) >= 1

    def test_normal_blink_rate_not_fatigue(self) -> None:
        """15 blinks/min → fatigue_indicator = False."""
        blink = BlinkSignal()
        blink._first_frame_time = time.time() - 60.0  # pretend 60s elapsed
        # Inject 15 blinks over 60 seconds
        now = time.time()
        for i in range(15):
            blink._blink_times.append(now - 60 + i * 4)
        result = blink.process(make_neutral_landmarks())
        assert result.fatigue_indicator is False

    def test_high_blink_rate_fatigue(self) -> None:
        """28 blinks/min → fatigue_indicator = True."""
        blink = BlinkSignal()
        blink._first_frame_time = time.time() - 60.0
        now = time.time()
        for i in range(28):
            blink._blink_times.append(now - 60 + i * 2)
        result = blink.process(make_neutral_landmarks())
        assert result.fatigue_indicator is True
        assert result.blink_rate_per_minute > 25

    def test_low_blink_rate_flow(self) -> None:
        """6 blinks/min → flow_indicator = True."""
        blink = BlinkSignal()
        blink._first_frame_time = time.time() - 60.0
        now = time.time()
        for i in range(6):
            blink._blink_times.append(now - 60 + i * 10)
        result = blink.process(make_neutral_landmarks())
        assert result.flow_indicator is True
        assert result.blink_rate_per_minute < 8

    def test_blink_rate_needs_60s_window(self) -> None:
        """Only 15s of data → confidence < 1.0 (not enough for full window)."""
        blink = BlinkSignal()
        blink._first_frame_time = time.time() - 10.0  # only 10s
        result = blink.process(make_neutral_landmarks())
        assert result.confidence < 1.0
