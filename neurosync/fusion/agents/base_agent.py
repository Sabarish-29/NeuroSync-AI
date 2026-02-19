"""
NeuroSync AI — Base agent protocol.

Every fusion agent inherits from ``BaseAgent`` and implements
``evaluate(state) -> AgentEvaluation``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from neurosync.fusion.state import AgentEvaluation, FusionState


class BaseAgent(ABC):
    """Abstract base for all fusion agents."""

    def __init__(self, agent_name: str, monitored_moments: list[str]) -> None:
        self.agent_name = agent_name
        self.monitored_moments = list(monitored_moments)
        self.last_detection: Optional[float] = None
        self.detection_count: int = 0

    # ── public API ──────────────────────────────────────────────────

    @abstractmethod
    async def evaluate(self, state: FusionState) -> AgentEvaluation:
        """Given current state decide whether to propose interventions."""
        ...

    # ── helpers ─────────────────────────────────────────────────────

    def is_on_cooldown(self, timestamp: float, cooldown_seconds: int) -> bool:
        """Return ``True`` if this agent fired recently."""
        if self.last_detection is None:
            return False
        return (timestamp - self.last_detection) < cooldown_seconds

    def record_detection(self, timestamp: float) -> None:
        """Update internal state after a proposal is accepted."""
        self.last_detection = timestamp
        self.detection_count += 1

    def _no_action(self, reasoning: str) -> AgentEvaluation:
        """Convenience: return an empty evaluation."""
        return AgentEvaluation(
            agent_name=self.agent_name,
            detected_moments=[],
            interventions=[],
            confidence=0.0,
            reasoning=reasoning,
        )
