"""
NeuroSync AI — Fusion Coordinator.

The main fusion loop called every 250 ms by the orchestrator.
Workflow:
    1. Build ``FusionState`` from all signal layers
    2. Execute graph (all 8 agents evaluate in parallel)
    3. Filter proposals by cooldowns
    4. Prioritise to max 2 non-conflicting interventions
    5. Return selected interventions to UI
"""

from __future__ import annotations

import time
from typing import Optional

from loguru import logger

from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.decision.cooldown import CooldownTracker
from neurosync.fusion.decision.conflict_resolver import ConflictResolver
from neurosync.fusion.decision.prioritizer import InterventionPrioritizer
from neurosync.fusion.graph import FusionGraph
from neurosync.fusion.state import (
    BehavioralSignals,
    FusionState,
    InterventionProposal,
    KnowledgeSignals,
    NLPSignals,
    WebcamSignals,
)


class FusionCoordinator:
    """Entry-point for every 250 ms fusion cycle."""

    def __init__(self, agents: list[BaseAgent]) -> None:
        self.graph = FusionGraph(agents)
        self.prioritizer = InterventionPrioritizer()
        self.cooldown_tracker = CooldownTracker()
        self.conflict_resolver = ConflictResolver()
        self.cycle_count: int = 0
        self._recent_fired: list[tuple[float, str]] = []  # (ts, moment_id)

    async def process_cycle(
        self,
        session_id: str,
        student_id: str,
        behavioral: BehavioralSignals,
        webcam: Optional[WebcamSignals] = None,
        knowledge: Optional[KnowledgeSignals] = None,
        nlp: Optional[NLPSignals] = None,
        lesson_position_ms: float = 0.0,
        session_duration_minutes: float = 0.0,
    ) -> list[InterventionProposal]:
        """Run one full fusion cycle and return selected interventions."""
        self.cycle_count += 1
        ts = time.time()

        state = FusionState(
            session_id=session_id,
            student_id=student_id,
            timestamp=ts,
            cycle_number=self.cycle_count,
            behavioral=behavioral,
            webcam=webcam,
            knowledge=knowledge or KnowledgeSignals(),
            nlp=nlp,
            session_duration_minutes=session_duration_minutes,
            lesson_position_ms=lesson_position_ms,
            recent_interventions=self._get_recent(ts),
            agent_states={},
        )

        # 1. Execute graph (all agents in parallel)
        result_state = await self.graph.execute(state)

        # 2. Filter by cooldowns
        available = self.cooldown_tracker.filter_interventions(
            result_state.proposed_interventions, ts,
        )

        # 3. Resolve conflicts
        compatible = self.conflict_resolver.resolve(available)

        # 4. Prioritise (max 2)
        selected = self.prioritizer.prioritize(compatible, max_interventions=2)

        # 5. Update cooldowns for fired interventions
        self.cooldown_tracker.update_from_fired(selected)
        for s in selected:
            self._recent_fired.append((ts, s.moment_id))

        logger.info(
            "Cycle {}: {} proposed → {} available → {} selected",
            self.cycle_count,
            len(result_state.proposed_interventions),
            len(available),
            len(selected),
        )

        return selected

    # ── helpers ─────────────────────────────────────────────────────

    def _get_recent(self, now: float, window: float = 300.0) -> list[str]:
        """Moment IDs fired in the last *window* seconds."""
        cutoff = now - window
        self._recent_fired = [
            (ts, mid) for ts, mid in self._recent_fired if ts >= cutoff
        ]
        return [mid for _, mid in self._recent_fired]
