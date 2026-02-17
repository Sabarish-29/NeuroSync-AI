"""
NeuroSync AI — Gaze direction detector.

Uses iris position relative to eye corners to determine where the
student is looking.  A rolling majority-vote window (default 30 frames)
prevents single-frame noise from triggering false positives.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np
from loguru import logger

from neurosync.config.settings import WEBCAM_THRESHOLDS
from neurosync.webcam.mediapipe_processor import (
    LEFT_EYE_INDICES,
    LEFT_IRIS_INDICES,
    RIGHT_EYE_INDICES,
    RIGHT_IRIS_INDICES,
    RawLandmarks,
)


GazeDirection = Literal["screen", "left", "right", "up", "down", "away"]


@dataclass
class GazeResult:
    """Output of the gaze signal processor."""

    horizontal_ratio: float = 0.5
    vertical_ratio: float = 0.5
    gaze_direction: GazeDirection = "screen"
    on_screen: bool = True
    off_screen_duration_ms: float = 0.0
    off_screen_triggered: bool = False
    confidence: float = 0.0


class GazeSignal:
    """
    Iris-ratio gaze estimator with rolling majority-vote smoothing.

    The horizontal and vertical ratios are computed from the relative
    iris position inside the eye bounding box.  A tolerance zone around
    0.5 is considered "looking at screen".
    """

    def __init__(self) -> None:
        self._tolerance: float = float(WEBCAM_THRESHOLDS["GAZE_SCREEN_CENTER_TOLERANCE"])
        self._trigger_ms: float = float(WEBCAM_THRESHOLDS["GAZE_OFF_SCREEN_TRIGGER_MS"])
        self._min_confidence: float = float(WEBCAM_THRESHOLDS["GAZE_CONFIDENCE_MINIMUM"])
        self._window_size: int = int(WEBCAM_THRESHOLDS["WEBCAM_FRAME_ROLLING_WINDOW"])

        # Rolling window of on-screen booleans (True = on screen)
        self._history: deque[bool] = deque(maxlen=self._window_size)

        # Off-screen tracking
        self._off_screen_start: Optional[float] = None
        self._off_screen_duration_ms: float = 0.0

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def process(self, landmarks: RawLandmarks) -> GazeResult:
        """Compute gaze direction from raw landmarks."""
        if not landmarks.face_detected or landmarks.face_landmarks is None:
            self._record_off_screen()
            return GazeResult(
                confidence=0.0,
                on_screen=False,
                off_screen_duration_ms=self._off_screen_duration_ms,
                off_screen_triggered=self._off_screen_duration_ms >= self._trigger_ms,
                gaze_direction="away",
            )

        lm = landmarks.face_landmarks
        try:
            h_ratio = self._horizontal_ratio(lm)
            v_ratio = self._vertical_ratio(lm)
        except (IndexError, ZeroDivisionError):
            self._record_off_screen()
            return GazeResult(confidence=0.0, on_screen=False, gaze_direction="away")

        direction = self._classify(h_ratio, v_ratio)
        on_screen = direction == "screen"

        if on_screen:
            self._record_on_screen()
        else:
            self._record_off_screen()

        # Majority vote: on-screen if >60% of recent window says on-screen
        self._history.append(on_screen)
        if len(self._history) >= 5:
            ratio_on = sum(self._history) / len(self._history)
            on_screen_smoothed = ratio_on > 0.60
        else:
            on_screen_smoothed = on_screen

        return GazeResult(
            horizontal_ratio=h_ratio,
            vertical_ratio=v_ratio,
            gaze_direction=direction,
            on_screen=on_screen_smoothed,
            off_screen_duration_ms=self._off_screen_duration_ms,
            off_screen_triggered=self._off_screen_duration_ms >= self._trigger_ms,
            confidence=1.0 if landmarks.face_detected else 0.0,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _horizontal_ratio(self, lm: list[tuple[float, float, float]]) -> float:
        """Iris centre X relative to eye width (0 = left, 1 = right)."""
        # Average of both eyes
        l_ratio = self._eye_iris_ratio_h(lm, LEFT_EYE_INDICES, LEFT_IRIS_INDICES)
        r_ratio = self._eye_iris_ratio_h(lm, RIGHT_EYE_INDICES, RIGHT_IRIS_INDICES)
        return (l_ratio + r_ratio) / 2.0

    def _vertical_ratio(self, lm: list[tuple[float, float, float]]) -> float:
        """Iris centre Y relative to eye height (0 = top, 1 = bottom)."""
        l_ratio = self._eye_iris_ratio_v(lm, LEFT_EYE_INDICES, LEFT_IRIS_INDICES)
        r_ratio = self._eye_iris_ratio_v(lm, RIGHT_EYE_INDICES, RIGHT_IRIS_INDICES)
        return (l_ratio + r_ratio) / 2.0

    @staticmethod
    def _eye_iris_ratio_h(
        lm: list[tuple[float, float, float]],
        eye_idx: list[int],
        iris_idx: list[int],
    ) -> float:
        eye_pts = np.array([lm[i][:2] for i in eye_idx])
        iris_pts = np.array([lm[i][:2] for i in iris_idx])
        iris_centre = iris_pts.mean(axis=0)
        x_min, x_max = eye_pts[:, 0].min(), eye_pts[:, 0].max()
        width = x_max - x_min
        if width < 1e-9:
            return 0.5
        return float((iris_centre[0] - x_min) / width)

    @staticmethod
    def _eye_iris_ratio_v(
        lm: list[tuple[float, float, float]],
        eye_idx: list[int],
        iris_idx: list[int],
    ) -> float:
        eye_pts = np.array([lm[i][:2] for i in eye_idx])
        iris_pts = np.array([lm[i][:2] for i in iris_idx])
        iris_centre = iris_pts.mean(axis=0)
        y_min, y_max = eye_pts[:, 1].min(), eye_pts[:, 1].max()
        height = y_max - y_min
        if height < 1e-9:
            return 0.5
        return float((iris_centre[1] - y_min) / height)

    def _classify(self, h: float, v: float) -> GazeDirection:
        centre = 0.5
        tol = self._tolerance
        if h < centre - tol:
            return "left"
        if h > centre + tol:
            return "right"
        if v < centre - tol:
            return "up"
        if v > centre + tol:
            return "down"
        return "screen"

    def _record_on_screen(self) -> None:
        self._off_screen_start = None
        self._off_screen_duration_ms = 0.0

    def _record_off_screen(self) -> None:
        now = time.time()
        if self._off_screen_start is None:
            self._off_screen_start = now
        self._off_screen_duration_ms = (now - self._off_screen_start) * 1000.0
