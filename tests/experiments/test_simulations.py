"""
Tests for simulations — StudentModel and ScenarioGenerator.
"""

from __future__ import annotations

import pytest

from neurosync.experiments.simulations.student_model import (
    StudentModel,
    StudentProfile,
)
from neurosync.experiments.simulations.scenario_generator import (
    Scenario,
    ScenarioGenerator,
    ScenarioStep,
)
from neurosync.fusion.state import BehavioralSignals, WebcamSignals
from neurosync.core.constants import (
    MOMENT_ATTENTION_DROP,
    MOMENT_COGNITIVE_OVERLOAD,
    MOMENT_FRUSTRATION,
    MOMENT_FATIGUE,
)


class TestStudentModel:
    """Unit tests for StudentModel."""

    def test_student_profile_defaults(self):
        """Default StudentProfile has sensible values."""
        p = StudentProfile()
        assert p.student_id == "sim_student"
        assert 0 < p.attention_baseline <= 1.0
        assert 0 <= p.frustration_tendency <= 1.0
        assert p.quiz_ability == 0.7
        assert p.seed == 42

    def test_advance_minute_increases_fatigue(self):
        """Each advance_minute call increases fatigue."""
        model = StudentModel(StudentProfile(fatigue_rate=0.2, seed=1))
        assert model.fatigue == 0.0
        model.advance_minute()
        assert model.fatigue > 0.0
        f1 = model.fatigue
        model.advance_minute()
        assert model.fatigue > f1

    def test_behavioral_signals_type(self):
        """get_behavioral_signals returns a BehavioralSignals instance."""
        model = StudentModel()
        model.advance_minute()
        signals = model.get_behavioral_signals()
        assert isinstance(signals, BehavioralSignals)
        assert hasattr(signals, "frustration_score")
        assert hasattr(signals, "fatigue_score")

    def test_webcam_signals_type(self):
        """get_webcam_signals returns a WebcamSignals instance."""
        model = StudentModel()
        signals = model.get_webcam_signals()
        assert isinstance(signals, WebcamSignals)
        assert hasattr(signals, "attention_score")
        assert signals.face_detected is True

    def test_answer_quiz_returns_bool(self):
        """answer_quiz returns a boolean value."""
        model = StudentModel()
        answers = [model.answer_quiz() for _ in range(10)]
        assert all(isinstance(a, bool) for a in answers)

    def test_reset_clears_state(self):
        """reset() restores initial state."""
        model = StudentModel(StudentProfile(seed=99))
        for _ in range(5):
            model.advance_minute()
        assert model.current_minute > 0
        assert model.fatigue > 0.0

        model.reset()
        assert model.current_minute == 0
        assert model.fatigue == 0.0
        assert model.frustration == 0.0

    def test_deterministic_with_same_seed(self):
        """Two models with same seed produce identical results."""
        m1 = StudentModel(StudentProfile(seed=42))
        m2 = StudentModel(StudentProfile(seed=42))
        for _ in range(10):
            m1.advance_minute()
            m2.advance_minute()
        assert m1.fatigue == m2.fatigue
        assert m1.frustration == m2.frustration


class TestScenarioGenerator:
    """Unit tests for ScenarioGenerator."""

    def test_attention_drop_scenario(self):
        """Attention drop scenario has correct structure."""
        s = ScenarioGenerator.attention_drop_scenario()
        assert isinstance(s, Scenario)
        assert s.name == "Attention Drop"
        assert MOMENT_ATTENTION_DROP in s.target_moments
        assert len(s.steps) == 3

    def test_cognitive_overload_scenario(self):
        """Cognitive overload scenario targets M02."""
        s = ScenarioGenerator.cognitive_overload_scenario()
        assert MOMENT_COGNITIVE_OVERLOAD in s.target_moments
        # At least one step should expect overload moment
        expected = [
            step for step in s.steps
            if MOMENT_COGNITIVE_OVERLOAD in step.expected_moments
        ]
        assert len(expected) >= 1

    def test_frustration_buildup_scenario(self):
        """Frustration scenario targets M07."""
        s = ScenarioGenerator.frustration_buildup_scenario()
        assert MOMENT_FRUSTRATION in s.target_moments
        assert s.duration_minutes == 15

    def test_full_session_scenario_hits_multiple_moments(self):
        """Full session scenario targets four+ moments."""
        s = ScenarioGenerator.full_session_scenario()
        assert len(s.target_moments) >= 4
        assert MOMENT_ATTENTION_DROP in s.target_moments
        assert MOMENT_FATIGUE in s.target_moments

    def test_all_scenarios_returns_four(self):
        """all_scenarios returns exactly 4 pre-built scenarios."""
        scenarios = ScenarioGenerator.all_scenarios()
        assert len(scenarios) == 4
        names = [s.name for s in scenarios]
        assert "Attention Drop" in names
        assert "Full Session" in names
