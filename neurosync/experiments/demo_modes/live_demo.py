"""
Live Demo — live demo mode with simulated signals.

Uses the StudentModel to generate realistic signals in real-time,
driving the NeuroSync orchestrator and displaying live results.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger

from neurosync.experiments.simulations.student_model import (
    StudentModel,
    StudentProfile,
)
from neurosync.fusion.orchestrator import NeuroSyncOrchestrator


@dataclass
class LiveDemoResult:
    """Outcome of a live demo session."""

    session_id: str
    duration_seconds: float
    cycles_run: int
    moments_fired: dict[str, int]
    interventions_total: int


class LiveDemo:
    """
    Live demo with simulated student signals fed into the orchestrator.

    Runs the full NeuroSync pipeline in real-time (or accelerated)
    so judges can see signals, moments, and interventions live.
    """

    def __init__(
        self,
        duration_minutes: int = 5,
        cycle_interval_ms: int = 250,
        realtime: bool = False,
        profile: Optional[StudentProfile] = None,
    ):
        self.duration_minutes = duration_minutes
        self.cycle_interval = cycle_interval_ms / 1000.0
        self.realtime = realtime
        self.profile = profile or StudentProfile(student_id="live_demo")
        self.student = StudentModel(self.profile)

    async def run(self) -> LiveDemoResult:
        """Run live demo driving the orchestrator with simulated signals."""
        session_id = f"live_demo_{int(time.time())}"
        orchestrator = NeuroSyncOrchestrator(
            session_id=session_id,
            student_id=self.profile.student_id,
        )

        total_cycles = int(self.duration_minutes * 60 / self.cycle_interval)
        moment_counts: dict[str, int] = {}
        total_interventions = 0
        start = time.time()

        for cycle in range(total_cycles):
            # Advance student model every ~60 cycles (1 minute)
            if cycle > 0 and cycle % int(60 / self.cycle_interval) == 0:
                self.student.advance_minute()

            behavioral = self.student.get_behavioral_signals()
            webcam = self.student.get_webcam_signals()

            interventions = await orchestrator.run_lesson_cycle(
                behavioral=behavioral,
                webcam=webcam,
            )

            for iv in interventions:
                mid = iv.moment_id
                moment_counts[mid] = moment_counts.get(mid, 0) + 1
                total_interventions += 1
                logger.info(
                    f"🎯 Cycle {cycle}: {mid} → {iv.intervention_type} "
                    f"(confidence={iv.confidence:.2f})"
                )

            if self.realtime:
                await asyncio.sleep(self.cycle_interval)

        elapsed = time.time() - start

        return LiveDemoResult(
            session_id=session_id,
            duration_seconds=round(elapsed, 2),
            cycles_run=total_cycles,
            moments_fired=moment_counts,
            interventions_total=total_interventions,
        )
