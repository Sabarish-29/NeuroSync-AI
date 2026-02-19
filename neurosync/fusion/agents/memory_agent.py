"""
NeuroSync AI — Memory Agent (M16).

Fires ``checkpoint_concepts`` when the NLP chunk tracker reports
that 4+ new concepts are unconfirmed in working memory.
"""

from __future__ import annotations

from neurosync.core.constants import MOMENT_WORKING_MEMORY_OVERFLOW
from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    FusionState,
    InterventionProposal,
)


class MemoryAgent(BaseAgent):
    """Monitors M16 — working memory overflow."""

    def __init__(self) -> None:
        super().__init__("memory_agent", [MOMENT_WORKING_MEMORY_OVERFLOW])

    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        if state.nlp is None or not state.nlp.overflow_risk:
            return self._no_action("No chunk overflow risk")

        proposal = InterventionProposal(
            moment_id=MOMENT_WORKING_MEMORY_OVERFLOW,
            agent_name=self.agent_name,
            intervention_type="checkpoint_concepts",
            urgency="high",
            confidence=0.85,
            payload={
                "unconfirmed_count": state.nlp.unconfirmed_count,
                "concepts_to_review": state.nlp.concepts_to_review[:4],
                "message": (
                    f"Let's consolidate these {state.nlp.unconfirmed_count} "
                    "concepts before adding more."
                ),
            },
            signals_supporting=["nlp_chunk_overflow"],
            cooldown_seconds=0,
            timestamp=state.timestamp,
        )

        self.record_detection(state.timestamp)

        return AgentEvaluation(
            agent_name=self.agent_name,
            detected_moments=[MOMENT_WORKING_MEMORY_OVERFLOW],
            interventions=[proposal],
            confidence=0.85,
            reasoning=f"Working memory overflow: {state.nlp.unconfirmed_count} unconfirmed",
        )
