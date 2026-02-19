"""
NeuroSync AI — Engagement Agent (M06, M07, M09).

Handles boredom (M06), frustration (M07), and confidence collapse (M09).
A single agent manages all three to prevent conflicting interventions.
"""

from __future__ import annotations

from neurosync.core.constants import (
    MOMENT_CONFIDENCE_COLLAPSE,
    MOMENT_FRUSTRATION,
    MOMENT_STEALTH_BOREDOM,
)
from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    FusionState,
    InterventionProposal,
)


class EngagementAgent(BaseAgent):
    """Monitors M06 (boredom), M07 (frustration), M09 (confidence collapse)."""

    COOLDOWN_SECONDS = 300  # 5 min between major engagement interventions

    def __init__(self) -> None:
        super().__init__(
            "engagement_agent",
            [MOMENT_STEALTH_BOREDOM, MOMENT_FRUSTRATION, MOMENT_CONFIDENCE_COLLAPSE],
        )

    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        interventions: list[InterventionProposal] = []
        detected: list[str] = []

        # M07 — frustration (highest priority, prevents dropout)
        if state.behavioral.frustration_score > 0.70:
            if not self.is_on_cooldown(state.timestamp, self.COOLDOWN_SECONDS):
                interventions.append(InterventionProposal(
                    moment_id=MOMENT_FRUSTRATION,
                    agent_name=self.agent_name,
                    intervention_type="rescue_frustration",
                    urgency="critical",
                    confidence=0.85,
                    payload={
                        "frustration_score": state.behavioral.frustration_score,
                        "message": "This is genuinely hard — that means you're growing!",
                        "method_switch": True,
                    },
                    signals_supporting=["behavioral_frustration", "webcam_tension"],
                    cooldown_seconds=self.COOLDOWN_SECONDS,
                    timestamp=state.timestamp,
                ))
                detected.append(MOMENT_FRUSTRATION)
                self.record_detection(state.timestamp)

        # M06 — boredom (student already knows this)
        elif state.knowledge.current_segment_mastery > 0.85:
            webcam_confirms = (
                state.webcam is not None
                and state.webcam.boredom_score > 0.60
            )
            if webcam_confirms or state.knowledge.current_segment_mastery > 0.90:
                interventions.append(InterventionProposal(
                    moment_id=MOMENT_STEALTH_BOREDOM,
                    agent_name=self.agent_name,
                    intervention_type="skip_to_challenge",
                    urgency="medium",
                    confidence=0.75 if webcam_confirms else 0.65,
                    payload={
                        "segment_mastery": state.knowledge.current_segment_mastery,
                        "message": "You already know this! Skip to harder part?",
                    },
                    signals_supporting=(
                        ["graph_high_mastery", "webcam_boredom"]
                        if webcam_confirms
                        else ["graph_high_mastery"]
                    ),
                    cooldown_seconds=180,
                    timestamp=state.timestamp,
                ))
                detected.append(MOMENT_STEALTH_BOREDOM)

        # M09 — confidence collapse (moderate frustration + progress underestimation)
        elif 0.45 < state.behavioral.frustration_score <= 0.70:
            interventions.append(InterventionProposal(
                moment_id=MOMENT_CONFIDENCE_COLLAPSE,
                agent_name=self.agent_name,
                intervention_type="show_knowledge_mirror",
                urgency="medium",
                confidence=0.70,
                payload={
                    "current_mastery_count": int(
                        state.knowledge.current_segment_mastery * 10,
                    ),
                    "message": "Let's see what you've actually learned so far.",
                },
                signals_supporting=["behavioral_frustration_medium"],
                cooldown_seconds=600,
                timestamp=state.timestamp,
            ))
            detected.append(MOMENT_CONFIDENCE_COLLAPSE)

        if interventions:
            return AgentEvaluation(
                agent_name=self.agent_name,
                detected_moments=detected,
                interventions=interventions,
                confidence=max(i.confidence for i in interventions),
                reasoning=f"Engagement interventions: {detected}",
            )

        return self._no_action("Engagement levels normal")
