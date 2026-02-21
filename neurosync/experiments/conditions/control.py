"""
Control condition — baseline (no AI intervention).

All NeuroSync features are disabled.  The student watches the lesson
video with no pauses, simplifications, or moments triggered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neurosync.experiments.framework import SessionConfig


@dataclass
class ControlCondition:
    """Configures a control (no-AI) session."""

    session_id: str
    student_id: str

    def build_session_config(self) -> SessionConfig:
        return SessionConfig(
            session_id=self.session_id,
            student_id=self.student_id,
            ai_enabled=False,
            webcam_enabled=False,
            eeg_enabled=False,
            experiment_group="control",
        )

    @staticmethod
    def apply_to_orchestrator(orchestrator: Any) -> None:
        """Disable all agents on an orchestrator instance."""
        if hasattr(orchestrator, "fusion") and hasattr(
            orchestrator.fusion, "agents"
        ):
            orchestrator.fusion.agents = []
