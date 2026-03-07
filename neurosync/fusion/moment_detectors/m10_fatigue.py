"""
M10: Fatigue Detection — Tiered Confidence.

Primary (behavioral): interaction variance (CoV), session duration,
idle frequency, performance decline.
EEG enhancement: elevated theta power (drowsiness marker).
"""

from __future__ import annotations

from typing import Optional

from neurosync.fusion.moment_detectors.base_detector import BaseMomentDetector
from neurosync.fusion.state import FusionState


class M10FatigueDetector(BaseMomentDetector):
    """Detects cognitive fatigue using tiered confidence."""

    VARIANCE_THRESHOLD = 0.65
    SESSION_RISK_START_MIN = 15.0
    SESSION_RISK_FULL_MIN = 35.0

    EEG_THETA_THRESHOLD = 0.50
    EEG_BOOST = 0.12

    def __init__(self) -> None:
        super().__init__(moment_id="M10", base_threshold=0.70)

    def detect_primary(self, state: FusionState) -> Optional[float]:
        variance_norm = min(1.0, state.behavioral.interaction_variance / self.VARIANCE_THRESHOLD)

        dur = state.session_duration_minutes
        if dur <= self.SESSION_RISK_START_MIN:
            duration_factor = 0.0
        elif dur >= self.SESSION_RISK_FULL_MIN:
            duration_factor = 1.0
        else:
            duration_factor = (dur - self.SESSION_RISK_START_MIN) / (
                self.SESSION_RISK_FULL_MIN - self.SESSION_RISK_START_MIN
            )

        idle_norm = min(1.0, state.behavioral.idle_frequency / 3.0)

        score = variance_norm * 0.50 + duration_factor * 0.25 + idle_norm * 0.25
        return score if score > 0.3 else None

    def detect_eeg_enhancement(self, state: FusionState) -> float:
        if state.eeg is None:
            return 0.0
        if state.eeg.theta_power > self.EEG_THETA_THRESHOLD:
            return self.EEG_BOOST
        return 0.0
