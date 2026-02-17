"""
NeuroSync AI — Micro-expression classifier.

Uses *geometric* landmark distance ratios (not a deep-learning model)
to classify learning-relevant expressions.  All distances are normalised
by face dimensions so results are scale-invariant.

An EMA (alpha = 0.3) smooths scores across frames.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
from loguru import logger

from neurosync.config.settings import WEBCAM_THRESHOLDS
from neurosync.webcam.mediapipe_processor import (
    CHIN,
    FOREHEAD,
    LEFT_CHEEK,
    LEFT_EYEBROW_INNER,
    LOWER_LIP,
    NOSE_TIP,
    RIGHT_CHEEK,
    RIGHT_EYEBROW_INNER,
    UPPER_LIP,
    LEFT_EYE_INDICES,
    RIGHT_EYE_INDICES,
    RawLandmarks,
)


ExpressionLabel = Literal["engaged", "frustrated", "confused", "bored", "neutral"]


@dataclass
class ExpressionResult:
    """Output of the expression signal processor."""

    frustration_tension: float = 0.0
    confusion_indicator: float = 0.0
    boredom_indicator: float = 0.0
    engagement_indicator: float = 0.0
    dominant_expression: ExpressionLabel = "neutral"
    confidence: float = 0.0


class ExpressionSignal:
    """
    Geometric ratio expression classifier with EMA smoothing.

    Detects: frustration tension, confusion, boredom, engagement.
    """

    def __init__(self) -> None:
        self._alpha: float = float(WEBCAM_THRESHOLDS["EXPRESSION_EMA_ALPHA"])
        self._frustration_thresh: float = float(WEBCAM_THRESHOLDS["EXPRESSION_FRUSTRATION_THRESHOLD"])
        self._boredom_thresh: float = float(WEBCAM_THRESHOLDS["EXPRESSION_BOREDOM_THRESHOLD"])

        # EMA state
        self._ema_frustration: float = 0.0
        self._ema_confusion: float = 0.0
        self._ema_boredom: float = 0.0
        self._ema_engagement: float = 0.0
        self._initialised: bool = False

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def process(self, landmarks: RawLandmarks) -> ExpressionResult:
        """Classify expression from raw face landmarks."""
        if not landmarks.face_detected or landmarks.face_landmarks is None:
            return ExpressionResult(confidence=0.0)

        lm = landmarks.face_landmarks
        try:
            raw = self._compute_raw_scores(lm)
        except (IndexError, ZeroDivisionError):
            return ExpressionResult(confidence=0.0)

        # Apply EMA smoothing
        frustration = self._update_ema("frustration", raw["frustration"])
        confusion = self._update_ema("confusion", raw["confusion"])
        boredom = self._update_ema("boredom", raw["boredom"])
        engagement = self._update_ema("engagement", raw["engagement"])

        dominant = self._classify(frustration, confusion, boredom, engagement)

        return ExpressionResult(
            frustration_tension=round(frustration, 4),
            confusion_indicator=round(confusion, 4),
            boredom_indicator=round(boredom, 4),
            engagement_indicator=round(engagement, 4),
            dominant_expression=dominant,
            confidence=1.0,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _compute_raw_scores(self, lm: list[tuple[float, float, float]]) -> dict[str, float]:
        """Compute raw (unsmoothed) expression scores from landmark distances."""
        face_width = self._dist(lm, LEFT_CHEEK, RIGHT_CHEEK)
        face_height = self._dist(lm, FOREHEAD, CHIN)
        if face_width < 1e-9 or face_height < 1e-9:
            return {"frustration": 0.0, "confusion": 0.0, "boredom": 0.0, "engagement": 0.5}

        # --- Frustration tension ---
        # Brow furrow: inner brows move closer together
        inner_brow_dist = self._dist(lm, LEFT_EYEBROW_INNER, RIGHT_EYEBROW_INNER) / face_width
        # Normalised baseline ~0.25; furrowed < 0.20
        brow_furrow = max(0.0, min(1.0, (0.25 - inner_brow_dist) / 0.10))

        # Lip press: lip gap decreases
        lip_gap = self._dist(lm, UPPER_LIP, LOWER_LIP) / face_height
        # Normalised baseline ~0.05; pressed < 0.02
        lip_press = max(0.0, min(1.0, (0.05 - lip_gap) / 0.04))

        # Brow lowering: distance from eyebrow to eye top decreases
        left_eye_top = np.array(lm[LEFT_EYE_INDICES[0]][:2])
        left_brow = np.array(lm[LEFT_EYEBROW_INNER][:2])
        brow_eye_dist = float(np.linalg.norm(left_brow - left_eye_top)) / face_height
        brow_lower = max(0.0, min(1.0, (0.08 - brow_eye_dist) / 0.05))

        frustration = brow_furrow * 0.40 + lip_press * 0.30 + brow_lower * 0.30

        # --- Confusion (asymmetric lip) ---
        left_lip_corner = np.array(lm[61][:2])   # left mouth corner
        right_lip_corner = np.array(lm[291][:2])  # right mouth corner
        lip_asymmetry = abs(left_lip_corner[1] - right_lip_corner[1]) / face_height
        # One brow raised: compare left vs right eyebrow-to-eye dist
        right_eye_top = np.array(lm[RIGHT_EYE_INDICES[0]][:2])
        right_brow = np.array(lm[RIGHT_EYEBROW_INNER][:2])
        right_brow_eye = float(np.linalg.norm(right_brow - right_eye_top)) / face_height
        brow_asymmetry = abs(brow_eye_dist - right_brow_eye) / max(brow_eye_dist, right_brow_eye, 1e-9)

        confusion = lip_asymmetry * 10.0 * 0.60 + brow_asymmetry * 0.40
        confusion = min(1.0, confusion)

        # --- Boredom ---
        jaw_drop = self._dist(lm, CHIN, NOSE_TIP) / face_height
        # Head droop: vertical position of nose relative to face centre
        nose_y = lm[NOSE_TIP][1]
        face_centre_y = (lm[FOREHEAD][1] + lm[CHIN][1]) / 2.0
        head_droop = max(0.0, (nose_y - face_centre_y) / 0.1)  # normalised

        # Reduced eye openness (heavy lids)
        left_ear = self._eye_openness(lm, LEFT_EYE_INDICES)
        right_ear = self._eye_openness(lm, RIGHT_EYE_INDICES)
        avg_ear = (left_ear + right_ear) / 2.0
        heavy_lids = max(0.0, min(1.0, (0.25 - avg_ear) / 0.10))

        boredom = heavy_lids * 0.35 + min(1.0, jaw_drop * 3.0) * 0.35 + min(1.0, head_droop) * 0.30

        # --- Engagement (inverse of boredom + lip press absence) ---
        engagement = max(0.0, 1.0 - boredom * 0.60 - frustration * 0.20 - confusion * 0.20)

        return {
            "frustration": max(0.0, min(1.0, frustration)),
            "confusion": max(0.0, min(1.0, confusion)),
            "boredom": max(0.0, min(1.0, boredom)),
            "engagement": max(0.0, min(1.0, engagement)),
        }

    def _update_ema(self, name: str, raw: float) -> float:
        """Update and return the EMA for the given score."""
        attr = f"_ema_{name}"
        prev = getattr(self, attr)
        if not self._initialised:
            setattr(self, attr, raw)
            return raw
        smoothed = self._alpha * raw + (1.0 - self._alpha) * prev
        setattr(self, attr, smoothed)
        return smoothed

    def process_and_mark_initialised(self, landmarks: RawLandmarks) -> ExpressionResult:
        """Process and mark EMA as initialised (call after first frame)."""
        result = self.process(landmarks)
        self._initialised = True
        return result

    @staticmethod
    def _dist(lm: list[tuple[float, float, float]], i: int, j: int) -> float:
        a = np.array(lm[i][:2])
        b = np.array(lm[j][:2])
        return float(np.linalg.norm(a - b))

    @staticmethod
    def _eye_openness(lm: list[tuple[float, float, float]], indices: list[int]) -> float:
        """Approximate eye openness from the vertical span of eye landmarks."""
        pts = np.array([lm[i][:2] for i in indices])
        y_range = pts[:, 1].max() - pts[:, 1].min()
        x_range = pts[:, 0].max() - pts[:, 0].min()
        if x_range < 1e-9:
            return 0.3
        return float(y_range / x_range)

    @staticmethod
    def _classify(
        frustration: float,
        confusion: float,
        boredom: float,
        engagement: float,
    ) -> ExpressionLabel:
        scores = {
            "frustrated": frustration,
            "confused": confusion,
            "bored": boredom,
            "engaged": engagement,
        }
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        if scores[best] < 0.25:
            return "neutral"
        return best  # type: ignore[return-value]
