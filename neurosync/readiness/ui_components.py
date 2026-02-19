"""
UI helper components for the readiness protocol.

Provides data structures that a front-end can consume to display
the readiness check flow, breathing animation, and results.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from neurosync.readiness.interventions.breathing import (
    TOTAL_DURATION,
    CYCLES,
    BreathPhase,
    phase_at,
)


class ReadinessUI(BaseModel):
    """Summary payload for the readiness check UI."""

    student_id: str
    lesson_topic: str
    readiness_pct: float = Field(0.0, ge=0.0, le=100.0)
    anxiety_pct: float = Field(0.0, ge=0.0, le=100.0)
    status_label: str = "Checking..."
    status_colour: str = "grey"
    show_breathing: bool = False
    breathing_total_seconds: float = TOTAL_DURATION
    breathing_cycles: int = CYCLES


def build_ui(
    student_id: str,
    lesson_topic: str,
    readiness: float,
    anxiety: float,
    status: str,
    show_breathing: bool = False,
) -> ReadinessUI:
    """Build a UI payload from raw readiness data."""
    colour_map = {
        "ready": "green",
        "not_ready": "orange",
        "needs_intervention": "red",
    }
    label_map = {
        "ready": "Ready to Learn!",
        "not_ready": "Warming Up…",
        "needs_intervention": "Let's Calm Down First",
    }
    return ReadinessUI(
        student_id=student_id,
        lesson_topic=lesson_topic,
        readiness_pct=round(readiness * 100, 1),
        anxiety_pct=round(anxiety * 100, 1),
        status_label=label_map.get(status, status),
        status_colour=colour_map.get(status, "grey"),
        show_breathing=show_breathing,
    )
