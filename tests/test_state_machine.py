"""
Step 5 — FusionGraph (state machine) tests (4 tests).
"""

from __future__ import annotations

import time

import pytest

from neurosync.fusion.agents.attention_agent import AttentionAgent
from neurosync.fusion.agents.engagement_agent import EngagementAgent
from neurosync.fusion.agents.fatigue_agent import FatigueAgent
from neurosync.fusion.agents.gap_agent import GapAgent
from neurosync.fusion.agents.memory_agent import MemoryAgent
from neurosync.fusion.agents.misconception_agent import MisconceptionAgent
from neurosync.fusion.agents.overload_agent import OverloadAgent
from neurosync.fusion.agents.plateau_agent import PlateauAgent
from neurosync.fusion.graph import FusionGraph
from neurosync.fusion.state import (
    BehavioralSignals,
    FusionState,
    KnowledgeSignals,
    NLPSignals,
    WebcamSignals,
)


def _all_agents():
    return [
        AttentionAgent(), OverloadAgent(), GapAgent(),
        EngagementAgent(), FatigueAgent(), MemoryAgent(),
        MisconceptionAgent(), PlateauAgent(),
    ]


def _multi_trigger_state() -> FusionState:
    """State that triggers multiple agents at once."""
    return FusionState(
        session_id="test",
        student_id="student",
        timestamp=time.time(),
        cycle_number=1,
        behavioral=BehavioralSignals(frustration_score=0.78, fatigue_score=0.80),
        webcam=WebcamSignals(off_screen_triggered=True, off_screen_duration_ms=5000, face_detected=True),
        knowledge=KnowledgeSignals(gaps_pending=["concept_x"], plateau_detected=True, plateau_concept_id="concept_y"),
        nlp=NLPSignals(overload_detected=True, target_simplification_phrase="phrase", max_complexity_score=0.9),
        session_duration_minutes=10,
        lesson_position_ms=50000,
    )


class TestFusionGraph:

    @pytest.mark.asyncio
    async def test_executes_all_agents(self):
        """All 8 agents run."""
        graph = FusionGraph(_all_agents())
        state = _multi_trigger_state()
        result = await graph.execute(state)
        assert len(result.agent_states) == 8

    @pytest.mark.asyncio
    async def test_aggregates_all_outputs(self):
        """Multi-trigger state → proposals from many agents."""
        graph = FusionGraph(_all_agents())
        result = await graph.execute(_multi_trigger_state())
        # Expect at least some proposals
        assert len(result.proposed_interventions) >= 3

    @pytest.mark.asyncio
    async def test_completes_in_under_100ms(self):
        """Performance: full graph < 100 ms."""
        graph = FusionGraph(_all_agents())
        state = _multi_trigger_state()
        start = time.perf_counter()
        await graph.execute(state)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 100, f"Graph took {elapsed_ms:.1f} ms"

    @pytest.mark.asyncio
    async def test_handles_agent_error_gracefully(self, normal_state: FusionState):
        """One agent raises → graph still completes."""

        class BrokenAgent(AttentionAgent):
            async def evaluate(self, state):
                raise RuntimeError("boom")

        agents = [BrokenAgent(), FatigueAgent()]
        graph = FusionGraph(agents)
        result = await graph.execute(normal_state)
        # Only the broken agent had an error, fatigue still ran
        assert "fatigue_agent" in result.agent_states
