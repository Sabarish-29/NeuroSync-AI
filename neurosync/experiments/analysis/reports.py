"""
Report Generator — produces summary reports of experiment results.

Outputs plain-text and structured reports.  PDF generation is optional
(requires reportlab).
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from loguru import logger

from neurosync.experiments.analysis.statistics import (
    ComparisonResult,
    ExperimentAnalysis,
)


class ReportGenerator:
    """Generate experiment analysis reports."""

    def __init__(self, output_dir: str = "experiment_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_text_report(
        self,
        experiment_id: str,
        comparisons: list[ComparisonResult],
        summary_rows: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate a plain-text report and return its path."""
        lines: list[str] = []
        lines.append(f"{'=' * 60}")
        lines.append(f"EXPERIMENT {experiment_id} — ANALYSIS REPORT")
        lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"{'=' * 60}")
        lines.append("")

        if summary_rows:
            lines.append("SUMMARY TABLE")
            lines.append("-" * 40)
            for row in summary_rows:
                for k, v in row.items():
                    lines.append(f"  {k}: {v}")
                lines.append("")

        lines.append("STATISTICAL COMPARISONS")
        lines.append("-" * 40)

        for c in comparisons:
            sig = "✓ Significant" if c.is_significant else "✗ Not significant"
            arrow = "⬆️" if c.percent_improvement > 0 else "⬇️"
            lines.append(f"  Metric: {c.metric}")
            lines.append(f"    Control:   {c.control_mean:.4f} ± {c.control_std:.4f}  (n={c.control_n})")
            lines.append(f"    Treatment: {c.treatment_mean:.4f} ± {c.treatment_std:.4f}  (n={c.treatment_n})")
            lines.append(f"    Change:    {arrow} {c.percent_improvement:+.2f}%")
            lines.append(f"    t = {c.t_statistic:.4f},  p = {c.p_value:.6f}  {sig}")
            lines.append(f"    Cohen's d = {c.cohens_d:.4f} ({c.effect_size_label})")
            lines.append("")

        path = self.output_dir / f"{experiment_id}_report.txt"
        path.write_text("\n".join(lines))
        logger.info(f"Report written → {path}")
        return str(path)

    def generate_json_report(
        self,
        experiment_id: str,
        comparisons: list[ComparisonResult],
    ) -> str:
        """Generate a JSON report."""
        data = {
            "experiment_id": experiment_id,
            "generated_at": time.time(),
            "comparisons": [asdict(c) for c in comparisons],
        }
        path = self.output_dir / f"{experiment_id}_report.json"
        path.write_text(json.dumps(data, indent=2))
        return str(path)
