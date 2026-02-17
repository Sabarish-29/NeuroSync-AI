"""
NeuroSync AI — Blink rate + eye fatigue detector.

Uses the Eye Aspect Ratio (EAR) computed from 6 eye landmark points.
A 60-second rolling window provides blinks-per-minute.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from loguru import logger

from neurosync.config.settings import WEBCAM_THRESHOLDS
from neurosync.webcam.mediapipe_processor import (
    LEFT_EAR_POINTS,
    RIGHT_EAR_POINTS,
    RawLandmarks,
)


@dataclass
class BlinkResult:
    """Output of the blink signal processor."""

    blink_rate_per_minute: float = 0.0
    ear_current: float = 0.3
    eye_state: Literal["open", "closed", "partially_closed"] = "open"
    fatigue_indicator: bool = False
    anxiety_indicator: bool = False
    flow_indicator: bool = False
    blink_irregularity: float = 0.0
    confidence: float = 0.0


class BlinkSignal:
    """
    EAR-based blink detector with 60-second rolling window.

    Normal blink rate: 12-20 blinks/min
    Fatigued: > 25 or < 8
    Anxious:  > 30 at rest
    Flow:     < 8 during active content
    """

    def __init__(self) -> None:
        self._ear_threshold: float = float(WEBCAM_THRESHOLDS["EAR_BLINK_THRESHOLD"])
        self._fatigue_high: float = float(WEBCAM_THRESHOLDS["BLINK_FATIGUE_HIGH_RATE"])
        self._fatigue_low: float = float(WEBCAM_THRESHOLDS["BLINK_FATIGUE_LOW_RATE"])
        self._anxiety_rate: float = float(WEBCAM_THRESHOLDS["BLINK_ANXIETY_RATE"])
        self._flow_rate: float = float(WEBCAM_THRESHOLDS["BLINK_FLOW_RATE"])

        # Rolling 60-second window of blink timestamps
        self._blink_times: deque[float] = deque()
        self._window_seconds: float = 60.0

        # State for consecutive-closed-frame detection
        self._consecutive_closed: int = 0
        self._blink_pending: bool = False

        # Inter-blink intervals for irregularity
        self._ibi: deque[float] = deque(maxlen=30)
        self._last_blink_time: float = 0.0

        # Track how long we've been collecting data
        self._first_frame_time: float = 0.0

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def process(self, landmarks: RawLandmarks) -> BlinkResult:
        """Compute blink metrics from face landmarks."""
        now = time.time()
        if self._first_frame_time == 0.0:
            self._first_frame_time = now

        if not landmarks.face_detected or landmarks.face_landmarks is None:
            return BlinkResult(confidence=0.0)

        lm = landmarks.face_landmarks

        try:
            left_ear = self._compute_ear(lm, LEFT_EAR_POINTS)
            right_ear = self._compute_ear(lm, RIGHT_EAR_POINTS)
        except (IndexError, ZeroDivisionError):
            return BlinkResult(confidence=0.0)

        ear = (left_ear + right_ear) / 2.0

        # Eye state
        if ear < self._ear_threshold:
            eye_state: Literal["open", "closed", "partially_closed"] = "closed"
            self._consecutive_closed += 1
        elif ear < self._ear_threshold + 0.05:
            eye_state = "partially_closed"
            self._consecutive_closed = 0
        else:
            eye_state = "open"
            # Detect completed blink (2-4 consecutive closed frames)
            if 2 <= self._consecutive_closed <= 8:
                self._register_blink(now)
            self._consecutive_closed = 0

        # Trim old blinks outside window
        cutoff = now - self._window_seconds
        while self._blink_times and self._blink_times[0] < cutoff:
            self._blink_times.popleft()

        # Blink rate
        elapsed = now - self._first_frame_time
        window = min(elapsed, self._window_seconds)
        if window > 0:
            blink_rate = len(self._blink_times) / (window / 60.0)
        else:
            blink_rate = 0.0

        # Irregularity: coefficient of variation of inter-blink intervals
        irregularity = 0.0
        if len(self._ibi) >= 3:
            arr = np.array(self._ibi)
            mean_ibi = arr.mean()
            if mean_ibi > 0:
                irregularity = float(arr.std() / mean_ibi)

        # Confidence — need at least 15s of data for reliable rate
        confidence = min(1.0, elapsed / 15.0)

        fatigue = blink_rate > self._fatigue_high or (blink_rate < self._fatigue_low and elapsed > 15)
        anxiety = blink_rate > self._anxiety_rate
        flow = blink_rate < self._flow_rate and elapsed > 15

        return BlinkResult(
            blink_rate_per_minute=round(blink_rate, 1),
            ear_current=round(ear, 4),
            eye_state=eye_state,
            fatigue_indicator=fatigue,
            anxiety_indicator=anxiety,
            flow_indicator=flow,
            blink_irregularity=round(irregularity, 4),
            confidence=round(confidence, 2),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_ear(
        lm: list[tuple[float, float, float]],
        indices: list[int],
    ) -> float:
        """
        Eye Aspect Ratio (EAR).

        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

        ``indices`` should contain 6 landmark indices ordered:
        p1 (left corner), p2 (upper-inner), p3 (upper-outer),
        p4 (right corner), p5 (lower-outer), p6 (lower-inner).
        """
        pts = [np.array(lm[i][:2]) for i in indices]
        p1, p2, p3, p4, p5, p6 = pts
        vertical_1 = np.linalg.norm(p2 - p6)
        vertical_2 = np.linalg.norm(p3 - p5)
        horizontal = np.linalg.norm(p1 - p4)
        if horizontal < 1e-9:
            return 0.3  # safe default
        return float((vertical_1 + vertical_2) / (2.0 * horizontal))

    def _register_blink(self, now: float) -> None:
        """Register a blink event and record inter-blink interval."""
        self._blink_times.append(now)
        if self._last_blink_time > 0:
            self._ibi.append(now - self._last_blink_time)
        self._last_blink_time = now
