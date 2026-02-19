"""
NeuroSync AI — Misconception Agent (M15).

Fires ``clear_misconception`` proactively before contradictory
content is delivered, preventing the student from reinforcing
a wrong mental model.
"""

from __future__ import annotations

from neurosync.core.constants import MOMENT_MISCONCEPTION
from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    FusionState,
    InterventionProposal,
)


class MisconceptionAgent(BaseAgent):
    """Monitors M15 — misconceptions."""

    def __init__(self) -> None:
        super().__init__("misconception_agent", [MOMENT_MISCONCEPTION])
        self.cleared_misconceptions: set[str] = set()

    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        if not state.knowledge.misconceptions_pending:
            return self._no_action("No misconceptions pending")

        interventions: list[InterventionProposal] = []

        for concept_id in state.knowledge.misconceptions_pending:
            if concept_id in self.cleared_misconceptions:
                continue

            interventions.append(InterventionProposal(
                moment_id=MOMENT_MISCONCEPTION,
                agent_name=self.agent_name,
                intervention_type="clear_misconception",
                urgency="high",
                confidence=0.75,
                payload={
                    "concept_id": concept_id,
                    "message": "Heads-up: there's a common misconception about this.",
                    "proactive": True,
                },
                signals_supporting=["graph_misconception_conflict"],
                cooldown_seconds=0,
                timestamp=state.timestamp,
            ))
            self.cleared_misconceptions.add(concept_id)

        if not interventions:
            return self._no_action("All misconceptions already cleared")

        self.record_detection(state.timestamp)

        return AgentEvaluation(
            agent_name=self.agent_name,
            detected_moments=[MOMENT_MISCONCEPTION] * len(interventions),
            interventions=interventions,
            confidence=0.75,
            reasoning=f"Clearing {len(interventions)} misconceptions",
        )
