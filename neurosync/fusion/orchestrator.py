"""
NeuroSync AI — High-level Orchestrator.

Ties together all signal layers (behavioural, webcam, graph, NLP)
and the fusion coordinator into the top-level lesson-playback loop.
"""

from __future__ import annotations

import time
from typing import Optional

from loguru import logger

from neurosync.fusion.agents.attention_agent import AttentionAgent
from neurosync.fusion.agents.engagement_agent import EngagementAgent
from neurosync.fusion.agents.fatigue_agent import FatigueAgent
from neurosync.fusion.agents.gap_agent import GapAgent
from neurosync.fusion.agents.memory_agent import MemoryAgent
from neurosync.fusion.agents.misconception_agent import MisconceptionAgent
from neurosync.fusion.agents.overload_agent import OverloadAgent
from neurosync.fusion.agents.plateau_agent import PlateauAgent
from neurosync.fusion.coordinator import FusionCoordinator
from neurosync.fusion.state import (
    BehavioralSignals,
    InterventionProposal,
    WebcamSignals,
)


def _build_default_agents() -> list:
    """Instantiate all 8 agents."""
    return [
        AttentionAgent(),
        OverloadAgent(),
        GapAgent(),
        EngagementAgent(),
        FatigueAgent(),
        MemoryAgent(),
        MisconceptionAgent(),
        PlateauAgent(),
    ]


class NeuroSyncOrchestrator:
    """
    Highest-level coordinator.  Call ``run_lesson_cycle()`` every
    250 ms during active lesson playback.
    """

    def __init__(
        self,
        session_id: str = "default",
        student_id: str = "student",
    ) -> None:
        self.session_id = session_id
        self.student_id = student_id
        self.agents = _build_default_agents()
        self.fusion = FusionCoordinator(self.agents)
        self.start_time = time.time()

        logger.info(
            "NeuroSyncOrchestrator initialised with {} agents",
            len(self.agents),
        )

    async def run_lesson_cycle(
        self,
        behavioral: Optional[BehavioralSignals] = None,
        webcam: Optional[WebcamSignals] = None,
    ) -> list[InterventionProposal]:
        """Main lesson loop iteration (called every 250 ms)."""
        session_minutes = (time.time() - self.start_time) / 60.0

        return await self.fusion.process_cycle(
            session_id=self.session_id,
            student_id=self.student_id,
            behavioral=behavioral or BehavioralSignals(),
            webcam=webcam,
            session_duration_minutes=session_minutes,
        )
