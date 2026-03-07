"""
M02: Cognitive Overload Detection — Tiered Confidence.

Primary (behavioral + webcam + NLP): rewind bursts, facial tension,
confused language.
EEG enhancement: high beta/alpha ratio (elevated cognitive load).

PATENT CLAIM 1.2: Multi-Modal Cognitive Overload Detection
===========================================================

NOVELTY:
Combines rewind burst detection, facial expression tension analysis, and
NLP confusion keyword scoring with optional EEG beta/alpha ratio monitoring,
providing specific cognitive overload detection distinct from generic
"confusion" states.

PRIMARY DETECTION PARAMETERS:
- REWIND_BURST_WEIGHT = 0.50
  Rationale: Rewind bursts (3+ rewinds in 30s) are the strongest single
  indicator of content being too complex. Students replay what they
  cannot absorb.

- EXPRESSION_TENSION_THRESHOLD = 0.60 (weight 0.30)
  Rationale: Furrowed brow / facial tension detected via MediaPipe
  face mesh landmarks correlates with high cognitive effort.
  Reference: Grafsgaard et al. (2013). Automatically recognizing facial
  expression: Predicting engagement and frustration. EDM 2013.

- NLP_CONFUSION_THRESHOLD = 0.50 (weight 0.20)
  Rationale: NLP confusion keywords ("what?", "I don't understand",
  "too fast") detected in student input text.

TARGET CONFIDENCE: 70-80% (primary detection only)

EEG ENHANCEMENT PARAMETERS (Optional):
- BETA_ALPHA_RATIO_THRESHOLD = 1.50
  Rationale: Beta/alpha ratio > 1.5 indicates elevated cognitive processing.
  Reference: Antonenko et al. (2010). Using EEG to measure cognitive load.
  Computers in Human Behavior.

- EEG_BOOST = 0.15 (+15%)
  Rationale: Highest EEG boost of all detectors because beta/alpha ratio
  is a well-established cognitive load biomarker.

TARGET CONFIDENCE WITH EEG: 85-95%

PRIOR ART DIFFERENTIATION:
- US11,328,606 (Pearson): Requires physiological sensors for load detection.
- Our innovation: Works with webcam+behavioral alone; EEG optional.

FILING STATUS: Provisional patent filed
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
