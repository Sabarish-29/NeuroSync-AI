"""
NeuroSync AI — Body posture + fidget detector.

Uses MediaPipe Pose landmarks (33 points) to detect:
- Head position (normal / forward lean / drooping)
- Shoulder tension (normal / raised / slumped)
- Fidgeting (high-variance landmark movement over 3 seconds)
- Forward slump
- Physical discomfort probability (M11)
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
from loguru import logger

from neurosync.config.settings import WEBCAM_THRESHOLDS
from neurosync.webcam.mediapipe_processor import RawLandmarks

# MediaPipe Pose landmark indices
POSE_NOSE = 0
POSE_LEFT_EAR = 7
POSE_RIGHT_EAR = 8
POSE_LEFT_SHOULDER = 11
POSE_RIGHT_SHOULDER = 12
POSE_LEFT_HIP = 23
POSE_RIGHT_HIP = 24


@dataclass
class PoseResult:
    """Output of the pose signal processor."""

    head_position: Literal["normal", "forward_lean", "drooping"] = "normal"
    shoulder_state: Literal["normal", "raised", "slumped"] = "normal"
    fidget_score: float = 0.0
    fidget_detected: bool = False
    forward_slump: bool = False
    physical_discomfort_probability: float = 0.0
    engagement_from_posture: float = 0.5
    confidence: float = 0.0


class PoseSignal:
    """
    Posture analyser using MediaPipe Pose landmarks.

    A rolling 90-frame window (3 s @ 30 fps) is used to compute
    fidget variance.
    """

    def __init__(self) -> None:
        self._window_size: int = int(WEBCAM_THRESHOLDS["POSTURE_WINDOW_FRAMES"])
        self._fidget_threshold: float = float(WEBCAM_THRESHOLDS["FIDGET_VARIANCE_THRESHOLD"])

        # Rolling positions for fidget detection (shoulder midpoint)
        self._positions: deque[np.ndarray] = deque(maxlen=self._window_size)

        # Baseline shoulder width (set on first good frame)
        self._baseline_shoulder_width: Optional[float] = None
        self._baseline_ear_shoulder_dist: Optional[float] = None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def process(self, landmarks: RawLandmarks) -> PoseResult:
        """Compute posture metrics from pose landmarks."""
        if not landmarks.pose_detected or landmarks.pose_landmarks is None:
            return PoseResult(confidence=0.0)

        plm = landmarks.pose_landmarks
        try:
            result = self._analyse(plm)
        except (IndexError, ZeroDivisionError):
            return PoseResult(confidence=0.0)

        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _analyse(self, plm: list[tuple[float, float, float]]) -> PoseResult:
        nose = np.array(plm[POSE_NOSE][:2])
        left_shoulder = np.array(plm[POSE_LEFT_SHOULDER][:2])
        right_shoulder = np.array(plm[POSE_RIGHT_SHOULDER][:2])
        left_ear = np.array(plm[POSE_LEFT_EAR][:2])
        right_ear = np.array(plm[POSE_RIGHT_EAR][:2])

        shoulder_mid = (left_shoulder + right_shoulder) / 2.0
        shoulder_width = float(np.linalg.norm(left_shoulder - right_shoulder))

        # Set baselines on first frame
        if self._baseline_shoulder_width is None:
            self._baseline_shoulder_width = shoulder_width

        ear_mid = (left_ear + right_ear) / 2.0
        ear_shoulder_dist = float(np.linalg.norm(ear_mid - shoulder_mid))
        if self._baseline_ear_shoulder_dist is None:
            self._baseline_ear_shoulder_dist = ear_shoulder_dist

        # --- Head position ---
        # Forward lean: nose is significantly forward (x in normalised coords)
        nose_shoulder_y_diff = nose[1] - shoulder_mid[1]
        if nose_shoulder_y_diff > 0.15:
            head_position: Literal["normal", "forward_lean", "drooping"] = "drooping"
        elif nose[1] < shoulder_mid[1] - 0.05:
            head_position = "forward_lean"
        else:
            head_position = "normal"

        # --- Shoulder tension ---
        if self._baseline_ear_shoulder_dist > 0:
            ratio = ear_shoulder_dist / self._baseline_ear_shoulder_dist
            if ratio < 0.80:
                shoulder_state: Literal["normal", "raised", "slumped"] = "raised"
            elif shoulder_width < self._baseline_shoulder_width * 0.85:
                shoulder_state = "slumped"
            else:
                shoulder_state = "normal"
        else:
            shoulder_state = "normal"

        # --- Fidget detection ---
        self._positions.append(shoulder_mid.copy())
        fidget_score = 0.0
        if len(self._positions) >= 10:
            pos_array = np.array(list(self._positions))
            variance = float(np.var(pos_array, axis=0).sum())
            fidget_score = min(1.0, variance / self._fidget_threshold)

        fidget_detected = fidget_score > 1.0 or (
            len(self._positions) >= 10 and fidget_score > 0.8
        )

        # --- Forward slump ---
        forward_slump = (
            shoulder_state == "slumped" or
            (head_position == "drooping" and shoulder_width < (self._baseline_shoulder_width or 1.0) * 0.90)
        )

        # --- Physical discomfort probability (M11) ---
        discomfort = 0.0
        if fidget_detected:
            discomfort += 0.40
        if shoulder_state == "raised":
            discomfort += 0.30
        if forward_slump:
            discomfort += 0.20
        if head_position == "drooping":
            discomfort += 0.10
        discomfort = min(1.0, discomfort)

        # --- Engagement from posture ---
        engagement = 0.5
        if head_position == "forward_lean":
            engagement = 0.8
        elif head_position == "drooping":
            engagement = 0.2
        if shoulder_state == "raised":
            engagement = max(0.0, engagement - 0.2)

        return PoseResult(
            head_position=head_position,
            shoulder_state=shoulder_state,
            fidget_score=round(min(1.0, fidget_score), 4),
            fidget_detected=fidget_detected,
            forward_slump=forward_slump,
            physical_discomfort_probability=round(discomfort, 4),
            engagement_from_posture=round(engagement, 2),
            confidence=1.0,
        )
