"""
Tests for statistical analysis — t-tests, effect sizes, reporting.
"""

from __future__ import annotations

import pytest

from neurosync.experiments.analysis.statistics import (
    ComparisonResult,
    ExperimentAnalysis,
)
from neurosync.experiments.framework import ExperimentResult


def _make_result(condition: str, quiz: float, completion: float = 0.9) -> ExperimentResult:
    """Helper to create a minimal ExperimentResult."""
    return ExperimentResult(
        experiment_id="E1",
        participant_id="P",
        condition=condition,
        session_id="s",
        quiz_score=quiz,
        completion_rate=completion,
        rewind_count=2,
        off_screen_time_seconds=30.0,
    )


class TestAnalysis:
    """Tests for ExperimentAnalysis."""

    def test_compare_groups_returns_result(self):
        """compare_groups returns a fully populated ComparisonResult."""
        ctrl = [_make_result("control", q) for q in [0.5, 0.55, 0.6, 0.45, 0.52]]
        treat = [_make_result("treatment", q) for q in [0.8, 0.85, 0.78, 0.82, 0.9]]

        result = ExperimentAnalysis.compare_groups(ctrl, treat, "quiz_score")

        assert isinstance(result, ComparisonResult)
        assert result.metric == "quiz_score"
        assert result.control_n == 5
        assert result.treatment_n == 5
        assert result.treatment_mean > result.control_mean

    def test_cohens_d_known_values(self):
        """Cohen's d matches expected value for simple data."""
        # Two groups: [1, 2, 3] vs [4, 5, 6]
        d = ExperimentAnalysis.cohens_d([1, 2, 3], [4, 5, 6])
        # d should be positive (group2 > group1) and large
        assert d > 2.0  # known value ≈ 3.0

    def test_effect_size_classification(self):
        """Effect sizes classified correctly against Cohen's thresholds."""
        assert ExperimentAnalysis.classify_effect_size(0.1) == "negligible"
        assert ExperimentAnalysis.classify_effect_size(0.3) == "small"
        assert ExperimentAnalysis.classify_effect_size(0.6) == "medium"
        assert ExperimentAnalysis.classify_effect_size(1.2) == "large"
        # Negative values use absolute
        assert ExperimentAnalysis.classify_effect_size(-0.9) == "large"

    def test_significance_detected(self):
        """Well-separated groups produce a significant p-value."""
        ctrl = [_make_result("control", q) for q in [0.3, 0.35, 0.28, 0.32, 0.31]]
        treat = [_make_result("treatment", q) for q in [0.9, 0.92, 0.88, 0.91, 0.87]]

        result = ExperimentAnalysis.compare_groups(ctrl, treat, "quiz_score")
        assert result.is_significant is True
        assert result.p_value < 0.05

    def test_summary_table_structure(self, sample_results):
        """Summary table has correct keys and row count."""
        groups = {
            "E1_control": [r for r in sample_results if r.condition == "control"],
            "E1_treatment": [r for r in sample_results if r.condition == "treatment"],
        }

        table = ExperimentAnalysis.generate_summary_table(groups)
        assert len(table) == 2

        for row in table:
            assert "condition" in row
            assert "n" in row
            assert "quiz_score_mean" in row
            assert "completion_rate_mean" in row

    def test_percent_improvement(self):
        """Percent improvement calculated correctly."""
        ctrl = [_make_result("control", q) for q in [0.50, 0.50, 0.50]]
        treat = [_make_result("treatment", q) for q in [0.75, 0.75, 0.75]]

        result = ExperimentAnalysis.compare_groups(ctrl, treat, "quiz_score")
        # (0.75 - 0.50) / 0.50 * 100 = 50%
        assert abs(result.percent_improvement - 50.0) < 0.1

    def test_insufficient_data_raises(self):
        """compare_groups raises ValueError with too few values."""
        ctrl = [_make_result("control", 0.5)]  # only 1 value
        treat = [_make_result("treatment", 0.8), _make_result("treatment", 0.9)]

        with pytest.raises(ValueError, match="Need ≥2 values"):
            ExperimentAnalysis.compare_groups(ctrl, treat, "quiz_score")
