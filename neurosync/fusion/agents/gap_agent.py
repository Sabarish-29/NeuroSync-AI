"""
NeuroSync AI — Gap Agent (M03).

Fires ``explain_concept`` proactively when the knowledge graph
reports unresolved prerequisite gaps.
"""

from __future__ import annotations

from neurosync.core.constants import MOMENT_KNOWLEDGE_GAP
from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    FusionState,
    InterventionProposal,
)


class GapAgent(BaseAgent):
    """Monitors M03 — knowledge gaps."""

    def __init__(self) -> None:
        super().__init__("gap_agent", [MOMENT_KNOWLEDGE_GAP])
        self.explained_concepts: set[str] = set()

    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        if not state.knowledge.gaps_pending:
            return self._no_action("No gaps detected")

        interventions: list[InterventionProposal] = []
        detected: list[str] = []

        for concept_id in state.knowledge.gaps_pending:
            if concept_id in self.explained_concepts:
                continue

            interventions.append(InterventionProposal(
                moment_id=MOMENT_KNOWLEDGE_GAP,
                agent_name=self.agent_name,
                intervention_type="explain_concept",
                urgency="high",
                confidence=0.80,
                payload={
                    "concept_id": concept_id,
                    "proactive": True,
                },
                signals_supporting=["nlp_entity_detected", "graph_gap_confirmed"],
                cooldown_seconds=0,
                timestamp=state.timestamp,
            ))
            detected.append(concept_id)
            self.explained_concepts.add(concept_id)

        if not interventions:
            return self._no_action("All gaps already explained")

        return AgentEvaluation(
            agent_name=self.agent_name,
            detected_moments=[MOMENT_KNOWLEDGE_GAP] * len(interventions),
            interventions=interventions,
            confidence=0.80,
            reasoning=f"Detected {len(detected)} new gaps: {detected}",
        )
