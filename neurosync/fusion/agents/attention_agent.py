"""
NeuroSync AI — Attention Agent (M01).

Fires ``pause_video`` when the student's gaze leaves the screen for ≥ 4 s.
Webcam is the primary signal; degrades gracefully when unavailable.
"""

from __future__ import annotations

from neurosync.core.constants import MOMENT_ATTENTION_DROP
from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    FusionState,
    InterventionProposal,
)


class AttentionAgent(BaseAgent):
    """Monitors M01 — attention drop via webcam gaze."""

    COOLDOWN_SECONDS = 120  # 2 min between pauses

    def __init__(self) -> None:
        super().__init__("attention_agent", [MOMENT_ATTENTION_DROP])

    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        # No webcam → cannot detect
        if state.webcam is None or not state.webcam.face_detected:
            return self._no_action("Webcam unavailable — cannot monitor attention")

        if not state.webcam.off_screen_triggered:
            return self._no_action("Student gaze on screen — attention OK")

        # Off-screen detected — cooldown check
        if self.is_on_cooldown(state.timestamp, self.COOLDOWN_SECONDS):
            return AgentEvaluation(
                agent_name=self.agent_name,
                detected_moments=[MOMENT_ATTENTION_DROP],
                interventions=[],
                confidence=0.7,
                reasoning="Attention drop detected but on cooldown",
            )

        proposal = InterventionProposal(
            moment_id=MOMENT_ATTENTION_DROP,
            agent_name=self.agent_name,
            intervention_type="pause_video",
            urgency="high",
            confidence=0.85,
            payload={
                "off_screen_duration_ms": state.webcam.off_screen_duration_ms,
                "message": "Ready to continue?",
                "resume_from_ms": state.lesson_position_ms,
            },
            signals_supporting=["webcam_gaze_off_screen"],
            cooldown_seconds=self.COOLDOWN_SECONDS,
            timestamp=state.timestamp,
        )

        self.record_detection(state.timestamp)

        return AgentEvaluation(
            agent_name=self.agent_name,
            detected_moments=[MOMENT_ATTENTION_DROP],
            interventions=[proposal],
            confidence=0.85,
            reasoning=f"Gaze off-screen for {state.webcam.off_screen_duration_ms:.0f} ms",
        )
