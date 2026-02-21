"""
Event Exporter — export experiment data to CSV / JSON.

Supports exporting individual sessions or batch experiment results
for external analysis (R, SPSS, etc.).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from loguru import logger


class EventExporter:
    """Exports experiment results to various formats."""

    def __init__(self, output_dir: str = "experiment_exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_results_csv(
        self,
        results: list[Any],
        filename: str = "experiment_results.csv",
    ) -> str:
        """
        Export ExperimentResult objects to CSV.

        Each row = one participant.
        """
        if not results:
            raise ValueError("No results to export")

        path = self.output_dir / filename

        fieldnames = [
            "experiment_id",
            "participant_id",
            "condition",
            "session_id",
            "quiz_score",
            "completion_rate",
            "time_spent_seconds",
            "rewind_count",
            "idle_time_seconds",
            "off_screen_time_seconds",
            "interventions_received",
            "self_reported_focus",
            "self_reported_difficulty",
            "self_reported_frustration",
            "retention_day_7",
            "retention_day_30",
        ]

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                row = {k: getattr(r, k, None) for k in fieldnames}
                writer.writerow(row)

        logger.info(f"Exported {len(results)} results → {path}")
        return str(path)

    def export_results_json(
        self,
        results: list[Any],
        filename: str = "experiment_results.json",
    ) -> str:
        """Export ExperimentResult objects to JSON."""
        from dataclasses import asdict

        path = self.output_dir / filename

        data = [asdict(r) for r in results]
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported {len(results)} results → {path}")
        return str(path)

    def export_moment_summary_csv(
        self,
        results: list[Any],
        filename: str = "moment_summary.csv",
    ) -> str:
        """Export moment firing frequencies across all participants."""
        from neurosync.core.constants import ALL_MOMENTS

        path = self.output_dir / filename

        fieldnames = ["participant_id", "condition"] + ALL_MOMENTS

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                row: dict[str, Any] = {
                    "participant_id": r.participant_id,
                    "condition": r.condition,
                }
                for m in ALL_MOMENTS:
                    row[m] = r.moments_fired.get(m, 0)
                writer.writerow(row)

        logger.info(f"Exported moment summary → {path}")
        return str(path)
