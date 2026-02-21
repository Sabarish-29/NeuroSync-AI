"""
Tests for experiment conditions — Control, Treatment, Ablation.
"""

from __future__ import annotations

import pytest

from neurosync.experiments.conditions.control import ControlCondition
from neurosync.experiments.conditions.treatment import TreatmentCondition
from neurosync.experiments.conditions.ablation import AblationCondition
from neurosync.experiments.framework import SessionConfig


class TestControlCondition:
    """Tests for ControlCondition."""

    def test_eeg_disabled(self):
        """Control sessions always disable EEG."""
        ctrl = ControlCondition(session_id="c1", student_id="s1")
        sc = ctrl.build_session_config()
        assert sc.eeg_enabled is False


class TestTreatmentCondition:
    """Tests for TreatmentCondition."""

    def test_eeg_disabled(self):
        """Treatment sessions disable EEG (not used in NeuroSync)."""
        treat = TreatmentCondition(session_id="t1", student_id="s1")
        sc = treat.build_session_config()
        assert sc.eeg_enabled is False


class TestAblationCondition:
    """Tests for AblationCondition."""

    def test_features_tuple_defined(self):
        """FEATURES tuple lists all known features."""
        assert "webcam" in AblationCondition.FEATURES
        assert "attention_agent" in AblationCondition.FEATURES
        assert "spaced_repetition" in AblationCondition.FEATURES

    def test_disable_multiple_features(self):
        """Multiple features can be disabled simultaneously."""
        abl = AblationCondition(
            session_id="a1",
            student_id="s1",
            disabled_features=["webcam", "attention_agent", "fatigue_agent"],
        )
        sc = abl.build_session_config()
        assert sc.webcam_enabled is False
        assert sc.ai_enabled is True  # AI still enabled for remaining agents

    def test_default_no_features_disabled(self):
        """Default ablation has empty disabled_features."""
        abl = AblationCondition(session_id="a2", student_id="s2")
        assert abl.disabled_features == []
        sc = abl.build_session_config()
        assert sc.webcam_enabled is True

    def test_apply_noop_without_fusion(self):
        """apply_to_orchestrator is safe on objects without fusion."""
        abl = AblationCondition(
            session_id="a3",
            student_id="s3",
            disabled_features=["attention_agent"],
        )

        class FakeOrchestrator:
            pass

        # Should not raise
        abl.apply_to_orchestrator(FakeOrchestrator())
