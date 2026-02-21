"""
Scripted Demo — pre-scripted 5-minute hackathon demo.

Runs through a complete learning journey demonstrating all key
NeuroSync moments (M01, M02, M07) with deterministic timing.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from neurosync.core.constants import (
    MOMENT_ATTENTION_DROP,
    MOMENT_COGNITIVE_OVERLOAD,
    MOMENT_FRUSTRATION,
)


@dataclass
class DemoStep:
    """One step in the scripted demo."""

    time_offset: float          # seconds from start
    action: str
    description: str = ""
    signals: dict[str, Any] = field(default_factory=dict)
    moment: Optional[str] = None
    intervention: Optional[str] = None


@dataclass
class DemoResult:
    """Outcome of a demo run."""

    moments_demonstrated: list[str]
    steps_executed: int
    duration_seconds: float
    success: bool


class ScriptedDemo:
    """
    Pre-scripted 5-minute demo for hackathon presentations.

    Simulates a complete learning journey hitting M01, M02, M07
    with deterministic timing for a guaranteed clean demo.
    """

    SCRIPT: list[DemoStep] = [
        # Minute 1: Normal learning
        DemoStep(0, "start_video", "Introduction to Photosynthesis"),
        DemoStep(10, "student_attentive", signals={"attention": 0.9}),
        DemoStep(30, "student_attentive", "Student engaged", {"attention": 0.85}),

        # Minute 2: Attention drop (M01)
        DemoStep(60, "look_away", "Student looks away from screen", {"attention": 0.2}),
        DemoStep(
            65,
            "trigger_moment",
            "Attention drop detected!",
            moment=MOMENT_ATTENTION_DROP,
            intervention="pause_video",
        ),
        DemoStep(70, "return_attention", "Student refocuses", {"attention": 0.85}),

        # Minute 3: Cognitive overload (M02)
        DemoStep(120, "complex_content", "Dense content begins", {"complexity": 0.9}),
        DemoStep(125, "show_confusion", "Student rewinds video", signals={"rewind": True}),
        DemoStep(
            130,
            "trigger_moment",
            "Cognitive overload detected!",
            moment=MOMENT_COGNITIVE_OVERLOAD,
            intervention="simplify_content",
        ),
        DemoStep(140, "simplified", "Simplified content shown", {"complexity": 0.4}),

        # Minute 4: Frustration building (M07)
        DemoStep(180, "difficult_section", "Hard problems", {"frustration": 0.75}),
        DemoStep(
            185,
            "trigger_moment",
            "Frustration detected!",
            moment=MOMENT_FRUSTRATION,
            intervention="rescue_frustration",
        ),
        DemoStep(200, "rescued", "Encouraging intervention shown", {"frustration": 0.2}),

        # Minute 5: Success and completion
        DemoStep(240, "comprehension", "Student understands", {"confidence": 0.9}),
        DemoStep(270, "quiz_start", "Post-lesson quiz"),
        DemoStep(290, "quiz_complete", "Quiz score: 88%", {"quiz_score": 0.88}),
        DemoStep(300, "complete_lesson", "Lesson complete!"),
    ]

    def __init__(self, realtime: bool = False):
        self.realtime = realtime
        self._steps_executed = 0

    async def run(self) -> DemoResult:
        """Execute the scripted demo."""
        start = time.time()
        moments_hit: list[str] = []
        prev_time = 0.0

        for step in self.SCRIPT:
            if self.realtime:
                delay = step.time_offset - prev_time
                if delay > 0:
                    await asyncio.sleep(delay)
            prev_time = step.time_offset

            self._steps_executed += 1

            if step.action == "trigger_moment" and step.moment:
                moments_hit.append(step.moment)
                logger.info(
                    f"🎯 [{step.time_offset}s] {step.description} "
                    f"→ {step.moment} → {step.intervention}"
                )
            else:
                logger.debug(
                    f"👤 [{step.time_offset}s] {step.action}: {step.description}"
                )

        elapsed = time.time() - start

        return DemoResult(
            moments_demonstrated=moments_hit,
            steps_executed=self._steps_executed,
            duration_seconds=round(elapsed, 2),
            success=True,
        )
