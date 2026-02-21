"""
Treatment condition — full NeuroSync.

All features enabled: webcam, all 8 agents, all 22 moments,
adaptive spaced repetition, readiness checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neurosync.experiments.framework import SessionConfig


@dataclass
class TreatmentCondition:
    """Configures a treatment (full NeuroSync) session."""

    session_id: str
    student_id: str

    def build_session_config(self) -> SessionConfig:
        return SessionConfig(
            session_id=self.session_id,
            student_id=self.student_id,
            ai_enabled=True,
            webcam_enabled=True,
            eeg_enabled=False,
            experiment_group="treatment",
        )

    @staticmethod
    def apply_to_orchestrator(orchestrator: Any) -> None:
        """Ensure all agents are active (default state)."""
        pass  # Orchestrator is fully active by default
