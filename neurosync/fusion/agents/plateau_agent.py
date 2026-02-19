"""
NeuroSync AI — Plateau Agent (M22).

Fires ``method_overhaul`` when the knowledge graph reports three
consecutive failures on the same concept, signalling a learning
plateau.
"""

from __future__ import annotations

from neurosync.core.constants import MOMENT_PLATEAU_ESCAPE
from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    FusionState,
    InterventionProposal,
)


class PlateauAgent(BaseAgent):
    """Monitors M22 — learning plateau."""

    def __init__(self) -> None:
        super().__init__("plateau_agent", [MOMENT_PLATEAU_ESCAPE])
        self.switched_concepts: set[str] = set()

    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        if not state.knowledge.plateau_detected:
            return self._no_action("No plateau detected")

        concept_id = state.knowledge.plateau_concept_id or "unknown"

        if concept_id in self.switched_concepts:
            return AgentEvaluation(
                agent_name=self.agent_name,
                detected_moments=[MOMENT_PLATEAU_ESCAPE],
                interventions=[],
                confidence=0.70,
                reasoning=f"Plateau on {concept_id} but method already switched",
            )

        proposal = InterventionProposal(
            moment_id=MOMENT_PLATEAU_ESCAPE,
            agent_name=self.agent_name,
            intervention_type="method_overhaul",
            urgency="high",
            confidence=0.80,
            payload={
                "concept_id": concept_id,
                "new_method": "story_analogy",
                "message": "Let's try a completely different approach.",
                "abandon_current_method": True,
            },
            signals_supporting=["graph_plateau_3_failures"],
            cooldown_seconds=0,
            timestamp=state.timestamp,
        )

        self.switched_concepts.add(concept_id)
        self.record_detection(state.timestamp)

        return AgentEvaluation(
            agent_name=self.agent_name,
            detected_moments=[MOMENT_PLATEAU_ESCAPE],
            interventions=[proposal],
            confidence=0.80,
            reasoning=f"Plateau on {concept_id} — switching method",
        )
