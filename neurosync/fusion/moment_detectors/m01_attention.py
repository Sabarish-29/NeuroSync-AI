"""
M01: Attention Drop Detection — Tiered Confidence.

Primary (webcam + behavioral): gaze off-screen, low attention, idle time.
EEG enhancement: elevated alpha power (relaxation / eyes closed).
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from neurosync.fusion.moment_detectors.base_detector import BaseMomentDetector
from neurosync.fusion.state import FusionState


class M01AttentionDetector(BaseMomentDetector):
    """Detects attention drop using tiered confidence."""

    # Primary thresholds
    WEBCAM_ATTENTION_THRESHOLD = 0.30
    OFF_SCREEN_DURATION_MS = 3000.0
    BEHAVIORAL_IDLE_MS = 5000.0

    # Fusion weights
    WEBCAM_WEIGHT = 0.60
    BEHAVIORAL_WEIGHT = 0.40

    # EEG enhancement
    EEG_ALPHA_INCREASE = 0.30  # 30 % above baseline
    EEG_BOOST = 0.12

    def __init__(self) -> None:
        super().__init__(moment_id="M01", base_threshold=0.70)
        self._alpha_baseline: Optional[float] = None

    # ── primary ───────────────────────────────────────────────────────

    def detect_primary(self, state: FusionState) -> Optional[float]:
        webcam_score = 0.0
        behavioral_score = 0.0

        if state.webcam is not None:
            if state.webcam.attention_score < self.WEBCAM_ATTENTION_THRESHOLD:
                webcam_score = 1.0 - state.webcam.attention_score
            if state.webcam.off_screen_duration_ms > self.OFF_SCREEN_DURATION_MS:
                dur_score = min(1.0, state.webcam.off_screen_duration_ms / 10000)
                webcam_score = max(webcam_score, dur_score)

        idle_ms = (
            state.behavioral.idle_frequency * 60_000
            if state.behavioral.idle_frequency > 0
            else 0.0
        )
        if idle_ms > self.BEHAVIORAL_IDLE_MS:
            behavioral_score = min(1.0, idle_ms / 10000)

        if webcam_score <= 0 and behavioral_score <= 0:
            return None

        if state.webcam is not None:
            return self.WEBCAM_WEIGHT * webcam_score + self.BEHAVIORAL_WEIGHT * behavioral_score
        return behavioral_score

    # ── EEG enhancement ───────────────────────────────────────────────

    def detect_eeg_enhancement(self, state: FusionState) -> float:
        if state.eeg is None:
            return 0.0

        alpha = state.eeg.alpha_power
        if self._alpha_baseline is None:
            self._alpha_baseline = alpha
            return 0.0

        if self._alpha_baseline > 0:
            increase = (alpha - self._alpha_baseline) / self._alpha_baseline
            if increase > self.EEG_ALPHA_INCREASE:
                return self.EEG_BOOST
        return 0.0
