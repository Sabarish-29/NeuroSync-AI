"""
Breathing exercise intervention.

4-4-6 pattern (inhale-hold-exhale) × 8 cycles = 112 seconds total.
Provides phase computation so a UI can display real-time guidance.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from neurosync.config.settings import READINESS_CONFIG

INHALE: float = float(READINESS_CONFIG["BREATHE_INHALE"])
HOLD: float = float(READINESS_CONFIG["BREATHE_HOLD"])
EXHALE: float = float(READINESS_CONFIG["BREATHE_EXHALE"])
CYCLES: int = int(READINESS_CONFIG["BREATHE_CYCLES"])
CYCLE_DURATION: float = INHALE + HOLD + EXHALE
TOTAL_DURATION: float = CYCLE_DURATION * CYCLES


class BreathPhase(str, Enum):
    """Current phase of the breathing cycle."""

    INHALE = "inhale"
    HOLD = "hold"
    EXHALE = "exhale"
    COMPLETE = "complete"


class BreathState(BaseModel):
    """Snapshot of breathing exercise state at a point in time."""

    elapsed_seconds: float = Field(0.0, ge=0.0)
    current_cycle: int = Field(1, ge=1)
    phase: BreathPhase = BreathPhase.INHALE
    phase_progress: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Fraction of current phase completed",
    )
    is_complete: bool = False


def total_duration_seconds() -> float:
    """Return the total exercise duration in seconds."""
    return TOTAL_DURATION


def phase_at(elapsed: float) -> BreathState:
    """Return the breathing state at *elapsed* seconds from start.

    Parameters
    ----------
    elapsed:
        Seconds since the exercise began (≥ 0).
    """
    elapsed = max(0.0, elapsed)

    if elapsed >= TOTAL_DURATION:
        return BreathState(
            elapsed_seconds=round(elapsed, 2),
            current_cycle=CYCLES,
            phase=BreathPhase.COMPLETE,
            phase_progress=1.0,
            is_complete=True,
        )

    cycle_index = int(elapsed // CYCLE_DURATION)
    within_cycle = elapsed - cycle_index * CYCLE_DURATION

    if within_cycle < INHALE:
        phase = BreathPhase.INHALE
        progress = within_cycle / INHALE
    elif within_cycle < INHALE + HOLD:
        phase = BreathPhase.HOLD
        progress = (within_cycle - INHALE) / HOLD
    else:
        phase = BreathPhase.EXHALE
        progress = (within_cycle - INHALE - HOLD) / EXHALE

    return BreathState(
        elapsed_seconds=round(elapsed, 2),
        current_cycle=cycle_index + 1,
        phase=phase,
        phase_progress=round(min(progress, 1.0), 4),
        is_complete=False,
    )
