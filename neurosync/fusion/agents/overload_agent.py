"""
NeuroSync AI — Overload Agent (M02).

Fires ``simplify_phrase`` when NLP detects high-complexity language
and behavioural / webcam signals confirm cognitive strain.
"""

from __future__ import annotations

from neurosync.core.constants import MOMENT_COGNITIVE_OVERLOAD
from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    FusionState,
    InterventionProposal,
)


class OverloadAgent(BaseAgent):
    """Monitors M02 — cognitive overload."""

    def __init__(self) -> None:
        super().__init__("overload_agent", [MOMENT_COGNITIVE_OVERLOAD])
        self.cooldown_per_phrase: dict[str, float] = {}

    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        if state.nlp is None or not state.nlp.overload_detected:
            return self._no_action("No overload detected by NLP")

        phrase = state.nlp.target_simplification_phrase
        if phrase is None:
            return AgentEvaluation(
                agent_name=self.agent_name,
                detected_moments=[MOMENT_COGNITIVE_OVERLOAD],
                interventions=[],
                confidence=0.6,
                reasoning="Overload detected but no target phrase identified",
            )

        # Per-phrase cooldown (5 min)
        if phrase in self.cooldown_per_phrase:
            if state.timestamp - self.cooldown_per_phrase[phrase] < 300:
                return AgentEvaluation(
                    agent_name=self.agent_name,
                    detected_moments=[MOMENT_COGNITIVE_OVERLOAD],
                    interventions=[],
                    confidence=0.7,
                    reasoning=f"Phrase '{phrase}' already simplified recently",
                )

        # Confidence boosted by supporting signals
        confidence = 0.70
        signals: list[str] = ["nlp_complexity_high"]

        if state.behavioral.response_time_trend == "increasing":
            confidence += 0.10
            signals.append("response_time_increasing")

        if state.webcam and state.webcam.frustration_boost > 0.5:
            confidence += 0.10
            signals.append("webcam_tension")

        proposal = InterventionProposal(
            moment_id=MOMENT_COGNITIVE_OVERLOAD,
            agent_name=self.agent_name,
            intervention_type="simplify_phrase",
            urgency="medium",
            confidence=min(confidence, 1.0),
            payload={
                "original_phrase": phrase,
                "complexity_score": state.nlp.max_complexity_score,
            },
            signals_supporting=signals,
            cooldown_seconds=0,  # per-phrase instead
            timestamp=state.timestamp,
        )

        self.cooldown_per_phrase[phrase] = state.timestamp
        self.record_detection(state.timestamp)

        return AgentEvaluation(
            agent_name=self.agent_name,
            detected_moments=[MOMENT_COGNITIVE_OVERLOAD],
            interventions=[proposal],
            confidence=min(confidence, 1.0),
            reasoning=f"Complexity {state.nlp.max_complexity_score:.2f} for: {phrase}",
        )
