"""
M10: Fatigue Detection — Tiered Confidence.

Primary (behavioral): interaction variance (CoV), session duration,
idle frequency, performance decline.
EEG enhancement: elevated theta power (drowsiness marker).

PATENT CLAIM 1.10: Behavioral Fatigue Detection with EEG Enhancement
=====================================================================

NOVELTY:
Uses interaction variance coefficient of variation, session duration
modelling, and idle frequency analysis to detect cognitive fatigue
without requiring physiological sensors, with optional EEG theta power
enhancement for research-grade accuracy.

PRIMARY DETECTION PARAMETERS:
- VARIANCE_THRESHOLD = 0.65
  Rationale: Interaction variance (coefficient of variation of response
  times) above 0.65 indicates inconsistent engagement associated with
  fatigue. Students respond erratically when tired.

- SESSION_RISK_START_MIN = 15.0 minutes
  Rationale: Cognitive performance begins declining after 15 minutes
  of sustained focused work.
  Reference: Wickens et al. (2004). An Introduction to Human Factors
  Engineering, Chapter 9: Attention and Time-on-Task.

- SESSION_RISK_FULL_MIN = 35.0 minutes
  Rationale: Full fatigue risk at 35+ minutes. Linear interpolation
  between 15 and 35 minutes models progressive onset.

- IDLE_FREQUENCY_CEILING = 3.0 events/min
  Rationale: Normalised idle frequency; > 3 events/minute indicates
  frequent disengagement typical of fatigued students.

- FUSION_WEIGHTS: 50% variance, 25% duration, 25% idle
  Rationale: Variance is the most sensitive fatigue indicator;
  duration and idle provide contextual confirmation.

- MINIMUM_SCORE_THRESHOLD = 0.30
  Rationale: Below 0.3 composite score, evidence insufficient.

TARGET CONFIDENCE: 70-75% (primary detection only)

EEG ENHANCEMENT PARAMETERS (Optional):
- EEG_THETA_THRESHOLD = 0.50
  Rationale: Elevated theta power (4-8 Hz) is a well-established
  drowsiness biomarker.
  Reference: Cajochen et al. (1995). EEG and ocular correlates of
  circadian melatonin phase and human performance decrements.
  Acta Physiologica Scandinavica.

- EEG_BOOST = 0.12 (+12%)
  Rationale: Theta-based confirmation adds physiological evidence.

TARGET CONFIDENCE WITH EEG: 82-87%

PRIOR ART DIFFERENTIATION:
- Existing fatigue detection relies on physiological sensors (heart rate,
  EDA, EEG) as primary modality.
- Our innovation: Behavioral-first detection using interaction variance,
  with physiological (EEG) as optional enhancement only.

FILING STATUS: Provisional patent filed
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
