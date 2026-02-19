"""
Physiological anxiety assessment — blink-rate analysis.

Uses the webcam blink-rate signal (blinks per minute) to estimate
anxiety.  Higher-than-normal blink rates correlate with elevated stress.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from neurosync.config.settings import READINESS_CONFIG

_LOW: float = float(READINESS_CONFIG["BLINK_RATE_LOW"])
_NORMAL_HIGH: float = float(READINESS_CONFIG["BLINK_RATE_NORMAL_HIGH"])
_ELEVATED: float = float(READINESS_CONFIG["BLINK_RATE_ELEVATED"])
_CAP: float = float(READINESS_CONFIG["BLINK_RATE_ANXIETY_CAP"])


class PhysiologicalResult(BaseModel):
    """Result of the blink-rate anxiety assessment."""

    blink_rate_bpm: float | None = Field(
        None, description="Measured blink rate (blinks/min), None if unavailable",
    )
    anxiety_score: float = Field(
        0.0, ge=0.0, le=1.0,
    )
    available: bool = Field(
        True, description="True when a webcam reading was obtained",
    )


def assess_blink_rate(blink_rate: float | None) -> PhysiologicalResult:
    """Map a blink-rate reading to an anxiety score.

    Ranges
    ------
    - ``< 12``   → 0.20  (very calm / under-aroused)
    - ``12-20``  → 0.30  (normal)
    - ``20-25``  → 0.60  (mildly elevated)
    - ``> 25``   → linearly scaled up to 1.0 (capped at 40 bpm)
    - ``None``   → 0.50 fallback (unavailable)
    """
    if blink_rate is None:
        return PhysiologicalResult(
            blink_rate_bpm=None, anxiety_score=0.50, available=False,
        )

    bpm = max(0.0, blink_rate)

    if bpm < _LOW:
        score = 0.20
    elif bpm <= _NORMAL_HIGH:
        score = 0.30
    elif bpm <= _ELEVATED:
        score = 0.60
    else:
        # Linear scale from 0.60 at _ELEVATED to 1.0 at _CAP
        t = min((bpm - _ELEVATED) / (_CAP - _ELEVATED), 1.0)
        score = 0.60 + 0.40 * t

    return PhysiologicalResult(
        blink_rate_bpm=round(bpm, 2),
        anxiety_score=round(score, 4),
        available=True,
    )
