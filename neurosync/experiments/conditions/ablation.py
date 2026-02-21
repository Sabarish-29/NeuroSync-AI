"""
Ablation condition — selectively disable features.

Used to measure the individual contribution of each component.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from neurosync.experiments.framework import SessionConfig


@dataclass
class AblationCondition:
    """Configures an ablation (partial NeuroSync) session."""

    session_id: str
    student_id: str
    disabled_features: list[str] = field(default_factory=list)

    # Known features that can be disabled
    FEATURES = (
        "webcam",
        "attention_agent",
        "overload_agent",
        "frustration_agent",
        "fatigue_agent",
        "spaced_repetition",
        "readiness_check",
    )

    def build_session_config(self) -> SessionConfig:
        return SessionConfig(
            session_id=self.session_id,
            student_id=self.student_id,
            ai_enabled=True,
            webcam_enabled="webcam" not in self.disabled_features,
            eeg_enabled=False,
            experiment_group="ablation",
        )

    def apply_to_orchestrator(self, orchestrator: Any) -> None:
        """Remove agents matching disabled features."""
        if not hasattr(orchestrator, "fusion"):
            return

        agent_feature_map = {
            "attention_agent": "AttentionAgent",
            "overload_agent": "OverloadAgent",
            "frustration_agent": "FrustrationAgent",
            "fatigue_agent": "FatigueAgent",
        }

        if hasattr(orchestrator.fusion, "agents"):
            orchestrator.fusion.agents = [
                a
                for a in orchestrator.fusion.agents
                if type(a).__name__
                not in [
                    agent_feature_map[f]
                    for f in self.disabled_features
                    if f in agent_feature_map
                ]
            ]
