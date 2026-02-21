"""
Experiment Visualizations — matplotlib/seaborn plots.

Generates publication-quality charts comparing experiment groups.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg")  # non-interactive backend
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None  # type: ignore[assignment]

try:
    import seaborn as sns
except ImportError:  # pragma: no cover
    sns = None  # type: ignore[assignment]


class ExperimentVisualizations:
    """Generate plots for experiment results."""

    def __init__(self) -> None:
        if sns is not None:
            sns.set_theme(style="whitegrid")
        if plt is not None:
            plt.rcParams["figure.figsize"] = (10, 6)

    def plot_metric_comparison(
        self,
        control_results: list[Any],
        treatment_results: list[Any],
        metric: str,
        title: str = "",
    ) -> Any:
        """Box plot comparing control vs treatment on *metric*."""
        if plt is None:
            raise ImportError("matplotlib is required for visualizations")

        fig, ax = plt.subplots()

        control_vals = [
            getattr(r, metric)
            for r in control_results
            if getattr(r, metric, None) is not None
        ]
        treatment_vals = [
            getattr(r, metric)
            for r in treatment_results
            if getattr(r, metric, None) is not None
        ]

        ax.boxplot(
            [control_vals, treatment_vals],
            labels=["Control", "NeuroSync"],
        )
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.set_title(title or f"{metric} — Control vs NeuroSync")

        plt.tight_layout()
        return fig

    def plot_moment_frequency(
        self,
        results: list[Any],
        title: str = "Moment Firing Frequency",
    ) -> Any:
        """Bar chart of moment firing totals."""
        if plt is None:
            raise ImportError("matplotlib is required for visualizations")

        moment_totals: dict[str, int] = {}
        for r in results:
            for mid, count in r.moments_fired.items():
                moment_totals[mid] = moment_totals.get(mid, 0) + count

        sorted_moments = sorted(
            moment_totals.items(), key=lambda x: x[1], reverse=True
        )

        fig, ax = plt.subplots()
        if sorted_moments:
            ids, counts = zip(*sorted_moments)
            ax.bar(ids, counts, color="#6366f1")
        ax.set_xlabel("Moment ID")
        ax.set_ylabel("Total Firings")
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=45)
        plt.tight_layout()
        return fig

    def plot_forgetting_curves(
        self,
        control_retention: list[float],
        treatment_retention: list[float],
        time_points: list[int],
    ) -> Any:
        """Line plot of retention over time (E3)."""
        if plt is None:
            raise ImportError("matplotlib is required for visualizations")

        fig, ax = plt.subplots()
        ax.plot(
            time_points,
            control_retention,
            "o-",
            label="Fixed Schedule",
            linewidth=2,
        )
        ax.plot(
            time_points,
            treatment_retention,
            "s-",
            label="NeuroSync Adaptive",
            linewidth=2,
            color="#6366f1",
        )
        ax.set_xlabel("Days Since Learning")
        ax.set_ylabel("Retention (%)")
        ax.set_title("Retention: Fixed vs Adaptive Scheduling")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def save_figure(self, fig: Any, path: str) -> str:
        """Save a figure to disk."""
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path
