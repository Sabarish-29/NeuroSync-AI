"""
Readiness scorer — combines all three assessment components into
a single readiness score and recommendation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from neurosync.config.settings import READINESS_CONFIG

_W_SELF: float = float(READINESS_CONFIG["WEIGHT_SELF_REPORT"])
_W_PHYS: float = float(READINESS_CONFIG["WEIGHT_PHYSIOLOGICAL"])
_W_BEHAV: float = float(READINESS_CONFIG["WEIGHT_BEHAVIORAL"])
_READY_THRESH: float = float(READINESS_CONFIG["READY_THRESHOLD"])
_ANXIETY_HIGH: float = float(READINESS_CONFIG["ANXIETY_HIGH_THRESHOLD"])


class ReadinessScore(BaseModel):
    """Combined readiness evaluation."""

    self_report_anxiety: float = Field(0.0, ge=0.0, le=1.0)
    physiological_anxiety: float = Field(0.0, ge=0.0, le=1.0)
    behavioral_anxiety: float = Field(0.0, ge=0.0, le=1.0)
    webcam_available: bool = True

    combined_anxiety: float = Field(0.0, ge=0.0, le=1.0)
    readiness: float = Field(1.0, ge=0.0, le=1.0)

    status: Literal["ready", "not_ready", "needs_intervention"] = "ready"
    recommendation: str = ""


def compute(
    self_report_anxiety: float,
    physiological_anxiety: float,
    behavioral_anxiety: float,
    webcam_available: bool = True,
) -> ReadinessScore:
    """Weighted combination of the three assessment axes.

    When the webcam is unavailable the physiological weight is
    redistributed equally between self-report and behavioural.
    """
    if webcam_available:
        w_self, w_phys, w_behav = _W_SELF, _W_PHYS, _W_BEHAV
    else:
        # Redistribute physiological weight
        w_self = _W_SELF + _W_PHYS / 2.0
        w_phys = 0.0
        w_behav = _W_BEHAV + _W_PHYS / 2.0

    combined = (
        w_self * self_report_anxiety
        + w_phys * physiological_anxiety
        + w_behav * behavioral_anxiety
    )
    combined = round(min(max(combined, 0.0), 1.0), 4)
    readiness = round(1.0 - combined, 4)

    # Determine status & recommendation
    if readiness >= _READY_THRESH:
        status: Literal["ready", "not_ready", "needs_intervention"] = "ready"
        recommendation = "Student is ready to begin the lesson."
    elif combined >= _ANXIETY_HIGH:
        status = "needs_intervention"
        recommendation = (
            "High anxiety detected. Recommend breathing exercise "
            "and/or prerequisite review before starting."
        )
    else:
        status = "not_ready"
        recommendation = (
            "Student is not fully ready. Consider a brief warm-up "
            "or difficulty adjustment."
        )

    return ReadinessScore(
        self_report_anxiety=round(self_report_anxiety, 4),
        physiological_anxiety=round(physiological_anxiety, 4),
        behavioral_anxiety=round(behavioral_anxiety, 4),
        webcam_available=webcam_available,
        combined_anxiety=combined,
        readiness=readiness,
        status=status,
        recommendation=recommendation,
    )
