"""
Tests for experiment protocols — E1 through E5 configurations and quiz data.
"""

from __future__ import annotations

import pytest

from neurosync.experiments.protocols.e1_attention import E1_CONFIG, E1_QUIZ
from neurosync.experiments.protocols.e2_overload import E2_CONFIG
from neurosync.experiments.protocols.e3_retention import E3_CONFIG
from neurosync.experiments.protocols.e4_frustration import E4_CONFIG
from neurosync.experiments.protocols.e5_transfer import E5_CONFIG
from neurosync.experiments.framework import ExperimentConfig


class TestE1Protocol:
    """Tests for the Attention Capture experiment."""

    def test_has_both_conditions(self):
        """E1 has control and treatment configs."""
        assert "control" in E1_CONFIG
        assert "treatment" in E1_CONFIG

    def test_control_is_control(self):
        """Control config has condition='control'."""
        assert E1_CONFIG["control"].condition == "control"
        assert E1_CONFIG["control"].experiment_id == "E1"

    def test_treatment_has_moments_metric(self):
        """Treatment config tracks moments_fired metric."""
        assert "moments_fired" in E1_CONFIG["treatment"].metrics

    def test_quiz_has_10_questions(self):
        """E1 quiz contains exactly 10 questions."""
        assert len(E1_QUIZ) == 10

    def test_quiz_correct_index_valid(self):
        """Each quiz question correct index is within options range."""
        for q in E1_QUIZ:
            assert "question" in q
            assert "options" in q
            assert "correct" in q
            assert 0 <= q["correct"] < len(q["options"])


class TestE2Protocol:
    """Tests for Cognitive Load Management experiment."""

    def test_duration_20_minutes(self):
        """E2 runs for 20 minutes."""
        assert E2_CONFIG["control"].duration_minutes == 20
        assert E2_CONFIG["treatment"].duration_minutes == 20


class TestE3Protocol:
    """Tests for Long-Term Retention experiment."""

    def test_has_retention_metrics(self):
        """E3 tracks retention_day_7 and retention_day_30."""
        metrics = E3_CONFIG["treatment"].metrics
        assert "retention_day_7" in metrics
        assert "retention_day_30" in metrics


class TestE4Protocol:
    """Tests for Frustration & Dropout Prevention experiment."""

    def test_duration_30_minutes(self):
        """E4 runs for 30 minutes."""
        assert E4_CONFIG["control"].duration_minutes == 30

    def test_tracks_dropout_rate(self):
        """E4 metrics include dropout_rate."""
        assert "dropout_rate" in E4_CONFIG["control"].metrics


class TestE5Protocol:
    """Tests for Transfer Learning experiment."""

    def test_has_transfer_metrics(self):
        """E5 tracks transfer_score and explanation_quality."""
        metrics = E5_CONFIG["treatment"].metrics
        assert "transfer_score" in metrics
        assert "explanation_quality" in metrics

    def test_sample_size_40(self):
        """E5 sample size is 40 per group."""
        assert E5_CONFIG["control"].sample_size == 40
