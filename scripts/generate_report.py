#!/usr/bin/env python3
"""
CLI: Generate an analysis report from experiment results.

Usage:
    python scripts/generate_report.py --experiment E1 --participants 20
    python scripts/generate_report.py --experiment E1 --participants 20 --output report.txt
"""

from __future__ import annotations

import argparse
import asyncio

from loguru import logger


async def main(experiment_id: str, num_participants: int, output: str | None) -> None:
    from neurosync.experiments.framework import ExperimentFramework
    from neurosync.experiments.analysis.statistics import ExperimentAnalysis
    from neurosync.experiments.analysis.reports import ReportGenerator

    logger.info(f"Generating report for {experiment_id}")

    framework = ExperimentFramework()
    results = await framework.run_batch(experiment_id, num_participants)

    control = [r for r in results if r.condition == "control"]
    treatment = [r for r in results if r.condition == "treatment"]

    analysis = ExperimentAnalysis()
    comparisons = []
    for metric in (
        "quiz_score", "completion_rate", "rewind_count",
        "off_screen_time_seconds", "idle_time_seconds",
    ):
        try:
            comp = analysis.compare_groups(control, treatment, metric)
            comparisons.append(comp)
        except ValueError:
            pass

    summary = analysis.generate_summary_table({
        f"{experiment_id}_control": control,
        f"{experiment_id}_treatment": treatment,
    })

    reporter = ReportGenerator()
    path = reporter.generate_text_report(experiment_id, comparisons, summary)
    print(f"Report generated → {path}")

    json_path = reporter.generate_json_report(experiment_id, comparisons)
    print(f"JSON report → {json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate experiment report")
    parser.add_argument("--experiment", required=True, help="Experiment ID (E1-E5)")
    parser.add_argument(
        "--participants", type=int, default=20, help="Number of participants"
    )
    parser.add_argument("--output", default=None, help="Output path (optional)")
    args = parser.parse_args()

    asyncio.run(main(args.experiment, args.participants, args.output))
