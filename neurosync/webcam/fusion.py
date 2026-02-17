"""
NeuroSync AI — Webcam multi-signal combiner.

Combines all 5 webcam signal processor outputs into moment-relevant
scores that map directly to the learning failure moments from Step 1.

Runs once per second (not every frame).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from loguru import logger

from neurosync.webcam.mediapipe_processor import RawLandmarks
from neurosync.webcam.signals.blink import BlinkResult, BlinkSignal
from neurosync.webcam.signals.expression import ExpressionResult, ExpressionSignal
from neurosync.webcam.signals.gaze import GazeResult, GazeSignal
from neurosync.webcam.signals.pose import PoseResult, PoseSignal
from neurosync.webcam.signals.rppg import RemotePPGSignal, RPPGResult


@dataclass
class WebcamMomentScores:
    """Aggregated webcam scores mapped to learning moments."""

    timestamp: float = 0.0
    attention_score: float = 0.0           # M01
    off_screen_triggered: bool = False
    off_screen_duration_ms: float = 0.0
    frustration_boost: float = 0.0         # M07 boost
    boredom_score: float = 0.0             # M06
    discomfort_probability: float = 0.0    # M11
    fatigue_boost: float = 0.0             # M10 boost
    heart_rate_bpm: Optional[float] = None
    face_detected: bool = False
    signal_quality_overall: float = 0.0


class WebcamFusionEngine:
    """
    Combines gaze, blink, expression, pose, and rPPG into moment scores.

    Usage::

        engine = WebcamFusionEngine(gaze, blink, expression, pose, rppg)
        scores = engine.compute(landmarks)            # face only
        scores = engine.compute(landmarks, frame=bgr) # face + rPPG
    """

    def __init__(
        self,
        gaze: GazeSignal,
        blink: BlinkSignal,
        expression: ExpressionSignal,
        pose: PoseSignal,
        rppg: RemotePPGSignal,
    ) -> None:
        self._gaze = gaze
        self._blink = blink
        self._expression = expression
        self._pose = pose
        self._rppg = rppg
        logger.debug("WebcamFusionEngine initialised")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def compute(
        self,
        landmarks: RawLandmarks,
        frame: Optional[np.ndarray] = None,
    ) -> WebcamMomentScores:
        """
        Run all processors and combine into moment-relevant scores.

        Parameters
        ----------
        landmarks:
            Output of ``MediaPipeProcessor.process_frame()``.
        frame:
            Raw BGR frame — required for rPPG forehead extraction.
        """
        if not landmarks.face_detected:
            return WebcamMomentScores(
                timestamp=landmarks.frame_timestamp,
                face_detected=False,
            )

        # Run each processor
        gaze_r = self._gaze.process(landmarks)
        blink_r = self._blink.process(landmarks)
        expr_r = self._expression.process(landmarks)
        pose_r = self._pose.process(landmarks)
        rppg_r = self._rppg.process(landmarks, frame=frame)

        # Fuse into moment scores
        return self._fuse(landmarks.frame_timestamp, gaze_r, blink_r, expr_r, pose_r, rppg_r)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _fuse(
        self,
        timestamp: float,
        gaze: GazeResult,
        blink: BlinkResult,
        expr: ExpressionResult,
        pose: PoseResult,
        rppg: RPPGResult,
    ) -> WebcamMomentScores:
        # ATTENTION (M01)
        on_screen_f = 1.0 if gaze.on_screen else 0.0
        fatigue_f = 1.0 if blink.fatigue_indicator else 0.0
        attention = (
            on_screen_f * 0.60
            + (1.0 - expr.boredom_indicator) * 0.25
            + (1.0 - fatigue_f) * 0.15
        )

        # FRUSTRATION BOOST (M07)
        shoulder_raised = 1.0 if pose.shoulder_state == "raised" else 0.0
        anxiety_f = 1.0 if blink.anxiety_indicator else 0.0
        frustration_boost = (
            expr.frustration_tension * 0.60
            + shoulder_raised * 0.25
            + anxiety_f * 0.15
        )

        # BOREDOM (M06)
        flow_inv = 0.0 if blink.flow_indicator else 1.0
        head_droop = 1.0 if pose.head_position == "drooping" else 0.0
        boredom = (
            expr.boredom_indicator * 0.40
            + flow_inv * 0.30
            + head_droop * 0.30
        )

        # PHYSICAL DISCOMFORT (M11)
        fidget_f = 1.0 if pose.fidget_detected else 0.0
        stress_f = 1.0 if rppg.stress_indicator else 0.0
        discomfort = (
            pose.physical_discomfort_probability * 0.50
            + fidget_f * 0.30
            + stress_f * 0.20
        )

        # FATIGUE BOOST (M10)
        slump_f = 1.0 if pose.forward_slump else 0.0
        fatigue_boost = (
            fatigue_f * 0.40
            + slump_f * 0.35
            + (1.0 - expr.engagement_indicator) * 0.25
        )

        # Overall quality: average confidence across processors with results
        qualities = [gaze.confidence, blink.confidence, expr.confidence, pose.confidence]
        if rppg.reliable:
            qualities.append(rppg.confidence)
        quality = float(np.mean(qualities)) if qualities else 0.0

        return WebcamMomentScores(
            timestamp=timestamp,
            attention_score=round(attention, 4),
            off_screen_triggered=gaze.off_screen_triggered,
            off_screen_duration_ms=gaze.off_screen_duration_ms,
            frustration_boost=round(frustration_boost, 4),
            boredom_score=round(boredom, 4),
            discomfort_probability=round(discomfort, 4),
            fatigue_boost=round(fatigue_boost, 4),
            heart_rate_bpm=rppg.heart_rate_bpm,
            face_detected=True,
            signal_quality_overall=round(quality, 4),
        )
