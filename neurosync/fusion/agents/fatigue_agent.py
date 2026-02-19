"""
NeuroSync AI — Fatigue Agent (M10).

Forces a mandatory 2-minute break when fatigue exceeds the critical
threshold, with a 20-minute cooldown between forced breaks.
"""

from __future__ import annotations

from neurosync.core.constants import MOMENT_FATIGUE
from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    FusionState,
    InterventionProposal,
)


class FatigueAgent(BaseAgent):
    """Monitors M10 — mental fatigue."""

    COOLDOWN_SECONDS = 1200  # 20 min between forced breaks

    def __init__(self) -> None:
        super().__init__("fatigue_agent", [MOMENT_FATIGUE])

    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        if state.behavioral.fatigue_score < 0.75:
            return self._no_action(
                f"Fatigue {state.behavioral.fatigue_score:.2f} below critical"
            )

        if self.is_on_cooldown(state.timestamp, self.COOLDOWN_SECONDS):
            return AgentEvaluation(
                agent_name=self.agent_name,
                detected_moments=[MOMENT_FATIGUE],
                interventions=[],
                confidence=0.80,
                reasoning="Fatigue critical but on break cooldown",
            )

        proposal = InterventionProposal(
            moment_id=MOMENT_FATIGUE,
            agent_name=self.agent_name,
            intervention_type="force_break",
            urgency="critical",
            confidence=0.90,
            payload={
                "fatigue_score": state.behavioral.fatigue_score,
                "session_duration_minutes": state.session_duration_minutes,
                "break_duration_seconds": 120,
                "message": "Your brain needs a 2-minute break.",
            },
            signals_supporting=[
                "behavioral_variance_erratic",
                "session_duration_long",
                "webcam_fatigue_boost",
            ],
            cooldown_seconds=self.COOLDOWN_SECONDS,
            timestamp=state.timestamp,
        )

        self.record_detection(state.timestamp)

        return AgentEvaluation(
            agent_name=self.agent_name,
            detected_moments=[MOMENT_FATIGUE],
            interventions=[proposal],
            confidence=0.90,
            reasoning=(
                f"CRITICAL fatigue {state.behavioral.fatigue_score:.2f} "
                f"after {state.session_duration_minutes:.1f} min"
            ),
        )
