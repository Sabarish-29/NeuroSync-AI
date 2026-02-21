"""
Tests for report generation and visualizations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from neurosync.experiments.analysis.reports import ReportGenerator
from neurosync.experiments.analysis.statistics import (
    ComparisonResult,
    ExperimentAnalysis,
)
from neurosync.experiments.analysis.visualizations import ExperimentVisualizations
from neurosync.experiments.framework import ExperimentResult


def _result(condition: str, quiz: float, **kwargs) -> ExperimentResult:
    return ExperimentResult(
        experiment_id="E1",
        participant_id="P",
        condition=condition,
        session_id="s",
        quiz_score=quiz,
        completion_rate=kwargs.get("completion_rate", 0.9),
        moments_fired=kwargs.get("moments_fired", {}),
    )


@pytest.fixture
def comparisons():
    ctrl = [_result("control", q) for q in [0.5, 0.55, 0.6, 0.45, 0.52]]
    treat = [_result("treatment", q) for q in [0.8, 0.85, 0.78, 0.82, 0.9]]
    return [ExperimentAnalysis.compare_groups(ctrl, treat, "quiz_score")]


class TestReportGenerator:
    """Tests for text and JSON report generation."""

    def test_text_report_created(self, tmp_path, comparisons):
        """generate_text_report writes a file and returns its path."""
        gen = ReportGenerator(output_dir=str(tmp_path / "reports"))
        path = gen.generate_text_report("E1", comparisons)
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "E1" in content
        assert "STATISTICAL COMPARISONS" in content

    def test_text_report_contains_metrics(self, tmp_path, comparisons):
        """Text report includes metric names and statistics."""
        gen = ReportGenerator(output_dir=str(tmp_path / "reports2"))
        path = gen.generate_text_report("E1", comparisons)
        content = Path(path).read_text()
        assert "quiz_score" in content
        assert "Cohen's d" in content

    def test_text_report_with_summary(self, tmp_path, comparisons):
        """Text report includes summary table when provided."""
        summary = [{"condition": "E1_control", "n": 5, "quiz_score_mean": 0.52}]
        gen = ReportGenerator(output_dir=str(tmp_path / "reports3"))
        path = gen.generate_text_report("E1", comparisons, summary_rows=summary)
        content = Path(path).read_text()
        assert "SUMMARY TABLE" in content

    def test_json_report_valid(self, tmp_path, comparisons):
        """generate_json_report writes valid JSON."""
        gen = ReportGenerator(output_dir=str(tmp_path / "json_reports"))
        path = gen.generate_json_report("E1", comparisons)
        assert Path(path).exists()
        with open(path) as f:
            data = json.load(f)
        assert data["experiment_id"] == "E1"
        assert len(data["comparisons"]) == 1

    def test_json_report_has_comparison_fields(self, tmp_path, comparisons):
        """JSON report comparison entries have all expected fields."""
        gen = ReportGenerator(output_dir=str(tmp_path / "json2"))
        path = gen.generate_json_report("E1", comparisons)
        with open(path) as f:
            data = json.load(f)
        comp = data["comparisons"][0]
        assert "metric" in comp
        assert "p_value" in comp
        assert "cohens_d" in comp
        assert "is_significant" in comp


class TestVisualizations:
    """Tests for experiment visualizations."""

    def test_metric_comparison_plot(self):
        """plot_metric_comparison returns a figure object."""
        viz = ExperimentVisualizations()
        ctrl = [_result("control", q) for q in [0.5, 0.6, 0.55]]
        treat = [_result("treatment", q) for q in [0.8, 0.85, 0.9]]
        fig = viz.plot_metric_comparison(ctrl, treat, "quiz_score")
        assert fig is not None

    def test_moment_frequency_plot(self):
        """plot_moment_frequency returns a figure with moment bars."""
        viz = ExperimentVisualizations()
        results = [
            _result("treatment", 0.8, moments_fired={"M01": 3, "M02": 1}),
            _result("treatment", 0.9, moments_fired={"M01": 2, "M07": 4}),
        ]
        fig = viz.plot_moment_frequency(results)
        assert fig is not None

    def test_forgetting_curves_plot(self):
        """plot_forgetting_curves returns a figure."""
        viz = ExperimentVisualizations()
        fig = viz.plot_forgetting_curves(
            control_retention=[100, 80, 60, 40],
            treatment_retention=[100, 90, 80, 70],
            time_points=[0, 1, 7, 30],
        )
        assert fig is not None

    def test_save_figure(self, tmp_path):
        """save_figure writes a PNG file."""
        viz = ExperimentVisualizations()
        ctrl = [_result("control", q) for q in [0.5, 0.6]]
        treat = [_result("treatment", q) for q in [0.8, 0.85]]
        fig = viz.plot_metric_comparison(ctrl, treat, "quiz_score")
        path = str(tmp_path / "chart.png")
        saved = viz.save_figure(fig, path)
        assert Path(saved).exists()
