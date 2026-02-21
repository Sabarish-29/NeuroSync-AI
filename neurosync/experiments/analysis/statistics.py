"""
Statistical Analysis — t-tests, ANOVA, effect sizes.

Compares control vs treatment groups on collected metrics
and produces publication-quality statistics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from scipy import stats


@dataclass
class ComparisonResult:
    """Result of comparing two groups on a metric."""

    metric: str
    control_mean: float
    treatment_mean: float
    control_std: float
    treatment_std: float
    control_n: int
    treatment_n: int
    t_statistic: float
    p_value: float
    cohens_d: float
    percent_improvement: float
    is_significant: bool
    effect_size_label: str  # "small", "medium", "large"


class ExperimentAnalysis:
    """Statistical analysis of experiment results."""

    @staticmethod
    def compare_groups(
        control_results: list[Any],
        treatment_results: list[Any],
        metric: str,
    ) -> ComparisonResult:
        """
        Compare control vs treatment on *metric* using independent t-test.

        Parameters
        ----------
        control_results : list of ExperimentResult (control group)
        treatment_results : list of ExperimentResult (treatment group)
        metric : attribute name on ExperimentResult (e.g. "quiz_score")
        """
        control_values = [
            getattr(r, metric)
            for r in control_results
            if getattr(r, metric, None) is not None
        ]
        treatment_values = [
            getattr(r, metric)
            for r in treatment_results
            if getattr(r, metric, None) is not None
        ]

        if len(control_values) < 2 or len(treatment_values) < 2:
            raise ValueError(
                f"Need ≥2 values per group; got {len(control_values)} control, "
                f"{len(treatment_values)} treatment for '{metric}'"
            )

        c_mean = float(np.mean(control_values))
        t_mean = float(np.mean(treatment_values))
        c_std = float(np.std(control_values, ddof=1))
        t_std = float(np.std(treatment_values, ddof=1))

        t_stat, p_val = stats.ttest_ind(
            control_values, treatment_values, equal_var=False
        )

        d = ExperimentAnalysis.cohens_d(control_values, treatment_values)

        pct = (
            ((t_mean - c_mean) / abs(c_mean)) * 100
            if c_mean != 0
            else 0.0
        )

        return ComparisonResult(
            metric=metric,
            control_mean=round(c_mean, 4),
            treatment_mean=round(t_mean, 4),
            control_std=round(c_std, 4),
            treatment_std=round(t_std, 4),
            control_n=len(control_values),
            treatment_n=len(treatment_values),
            t_statistic=round(float(t_stat), 4),
            p_value=round(float(p_val), 6),
            cohens_d=round(d, 4),
            percent_improvement=round(pct, 2),
            is_significant=float(p_val) < 0.05,
            effect_size_label=ExperimentAnalysis.classify_effect_size(d),
        )

    @staticmethod
    def cohens_d(group1: list[float], group2: list[float]) -> float:
        """Compute Cohen's d effect size."""
        n1, n2 = len(group1), len(group2)
        var1 = float(np.var(group1, ddof=1))
        var2 = float(np.var(group2, ddof=1))
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        if pooled_std == 0:
            return 0.0
        return float((np.mean(group2) - np.mean(group1)) / pooled_std)

    @staticmethod
    def classify_effect_size(d: float) -> str:
        """Classify Cohen's d as small / medium / large."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"

    @staticmethod
    def generate_summary_table(
        experiment_results: dict[str, list[Any]],
    ) -> list[dict[str, Any]]:
        """
        Generate a summary statistics table.

        Parameters
        ----------
        experiment_results : {"E1_control": [results], "E1_treatment": [...], ...}

        Returns list of dicts (one per condition).
        """
        rows: list[dict[str, Any]] = []

        for condition_name, results in experiment_results.items():
            quiz_scores = [
                r.quiz_score for r in results if r.quiz_score is not None
            ]
            row: dict[str, Any] = {
                "condition": condition_name,
                "n": len(results),
                "quiz_score_mean": round(float(np.mean(quiz_scores)), 4)
                if quiz_scores
                else None,
                "quiz_score_std": round(float(np.std(quiz_scores, ddof=1)), 4)
                if len(quiz_scores) > 1
                else None,
                "completion_rate_mean": round(
                    float(np.mean([r.completion_rate for r in results])), 4
                ),
                "rewind_count_mean": round(
                    float(np.mean([r.rewind_count for r in results])), 2
                ),
                "off_screen_time_mean": round(
                    float(
                        np.mean(
                            [r.off_screen_time_seconds for r in results]
                        )
                    ),
                    2,
                ),
            }
            rows.append(row)

        return rows
