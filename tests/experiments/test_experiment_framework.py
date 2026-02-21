"""
Tests for the experiment framework core — configs, sessions, protocols.
"""

from __future__ import annotations

import pytest

from neurosync.experiments.framework import (
    BehavioralMetrics,
    ExperimentConfig,
    ExperimentFramework,
    ExperimentResult,
    SelfReportData,
    SessionConfig,
)
from neurosync.experiments.conditions.control import ControlCondition
from neurosync.experiments.conditions.treatment import TreatmentCondition
from neurosync.experiments.conditions.ablation import AblationCondition


# ── Config & Session ─────────────────────────────────────────────────


class TestExperimentFramework:
    """Unit tests for ExperimentFramework."""

    def test_experiment_config_defaults(self):
        """ExperimentConfig has sensible default values."""
        cfg = ExperimentConfig(
            experiment_id="E1",
            name="Test",
            hypothesis="H0",
        )
        assert cfg.condition == "control"
        assert cfg.duration_minutes == 15
        assert cfg.sample_size == 30
        assert "quiz_score" in cfg.metrics
        assert cfg.ablation_features == []

    def test_control_session_disables_ai(self):
        """ControlCondition produces a SessionConfig with AI disabled."""
        ctrl = ControlCondition(session_id="s1", student_id="stu")
        sc = ctrl.build_session_config()
        assert sc.ai_enabled is False
        assert sc.webcam_enabled is False
        assert sc.experiment_group == "control"

    def test_treatment_session_enables_ai(self):
        """TreatmentCondition produces a SessionConfig with AI enabled."""
        treat = TreatmentCondition(session_id="s2", student_id="stu")
        sc = treat.build_session_config()
        assert sc.ai_enabled is True
        assert sc.webcam_enabled is True
        assert sc.experiment_group == "treatment"

    def test_ablation_selectively_disables_webcam(self):
        """AblationCondition disables webcam when specified."""
        abl = AblationCondition(
            session_id="s3",
            student_id="stu",
            disabled_features=["webcam"],
        )
        sc = abl.build_session_config()
        assert sc.ai_enabled is True
        assert sc.webcam_enabled is False
        assert sc.experiment_group == "ablation"

    @pytest.mark.asyncio
    async def test_run_experiment_returns_result(self, framework, control_config):
        """run_experiment returns a populated ExperimentResult."""
        result = await framework.run_experiment(control_config)
        assert isinstance(result, ExperimentResult)
        assert result.experiment_id == "E1"
        assert result.condition == "control"
        assert result.participant_id == "P000"
        assert 0 <= result.completion_rate <= 1.0

    @pytest.mark.asyncio
    async def test_run_batch_splits_control_treatment(self, framework):
        """run_batch assigns half control, half treatment."""
        results = await framework.run_batch("E1", num_participants=6)
        conditions = [r.condition for r in results]
        assert conditions.count("control") == 3
        assert conditions.count("treatment") == 3

    def test_load_all_five_protocols(self, framework):
        """All five protocols (E1-E5) load successfully."""
        for eid in ExperimentFramework.EXPERIMENT_IDS:
            ctrl = framework.load_protocol(eid, "control")
            treat = framework.load_protocol(eid, "treatment")
            assert ctrl.experiment_id == eid
            assert treat.experiment_id == eid
            assert ctrl.condition == "control"
            assert treat.condition == "treatment"

    def test_unknown_experiment_raises(self, framework):
        """Loading an unknown experiment ID raises ValueError."""
        with pytest.raises(ValueError, match="Unknown experiment"):
            framework.load_protocol("E99", "control")
