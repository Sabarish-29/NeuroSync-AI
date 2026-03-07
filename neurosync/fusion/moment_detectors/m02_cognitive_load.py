"""
M02: Cognitive Overload Detection — Tiered Confidence.

Primary (behavioral + webcam + NLP): rewind bursts, facial tension,
confused language.
EEG enhancement: high beta/alpha ratio (elevated cognitive load).
"""

from __future__ import annotations

from typing import Optional

from neurosync.fusion.moment_detectors.base_detector import BaseMomentDetector
from neurosync.fusion.state import FusionState


class M02CognitiveLoadDetector(BaseMomentDetector):
    """Detects cognitive overload using tiered confidence."""

    EXPRESSION_TENSION_THRESHOLD = 0.6
    BETA_ALPHA_RATIO_THRESHOLD = 1.5
    EEG_BOOST = 0.15

    def __init__(self) -> None:
        super().__init__(moment_id="M02", base_threshold=0.70)

    def detect_primary(self, state: FusionState) -> Optional[float]:
        score = 0.0

        if state.behavioral.rewind_burst:
            score += 0.50

        if state.webcam is not None:
            if state.webcam.frustration_boost > self.EXPRESSION_TENSION_THRESHOLD:
                score += 0.30

        if state.nlp is not None:
            if state.nlp.confusion_score > 0.5:
                score += 0.20

        return score if score > 0 else None

    def detect_eeg_enhancement(self, state: FusionState) -> float:
        if state.eeg is None:
            return 0.0
        alpha = state.eeg.alpha_power
        if alpha > 0:
            ratio = state.eeg.beta_power / alpha
            if ratio > self.BETA_ALPHA_RATIO_THRESHOLD:
                return self.EEG_BOOST
        return 0.0
