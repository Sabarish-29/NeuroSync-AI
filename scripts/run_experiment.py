#!/usr/bin/env python3
"""
CLI: Run an experiment by ID.

Usage:
    python scripts/run_experiment.py --experiment E1 --participants 10
    python scripts/run_experiment.py --experiment E3 --participants 50
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from loguru import logger


async def main(experiment_id: str, num_participants: int) -> None:
    from neurosync.experiments.framework import ExperimentFramework
    from neurosync.experiments.analysis.statistics import ExperimentAnalysis
    from neurosync.experiments.data_collection.event_exporter import EventExporter

    logger.info(
        f"Running experiment {experiment_id} with {num_participants} participants"
    )

    framework = ExperimentFramework()
    results = await framework.run_batch(experiment_id, num_participants)

    # Split into groups
    control = [r for r in results if r.condition == "control"]
    treatment = [r for r in results if r.condition == "treatment"]

    logger.info(f"Control: {len(control)}, Treatment: {len(treatment)}")

    # Analyse
    analysis = ExperimentAnalysis()
    for metric in ("quiz_score", "completion_rate", "off_screen_time_seconds"):
        try:
            comp = analysis.compare_groups(control, treatment, metric)
            sig = "✓ Significant" if comp.is_significant else "✗ Not significant"
            print(
                f"  {metric}: control={comp.control_mean:.3f}, "
                f"treatment={comp.treatment_mean:.3f}, "
                f"Δ={comp.percent_improvement:+.1f}%, "
                f"p={comp.p_value:.4f} {sig}, "
                f"d={comp.cohens_d:.2f} ({comp.effect_size_label})"
            )
        except ValueError as e:
            logger.warning(f"Skipped {metric}: {e}")

    # Export
    exporter = EventExporter()
    csv_path = exporter.export_results_csv(results, f"{experiment_id}_results.csv")
    print(f"\nResults exported → {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a NeuroSync experiment")
    parser.add_argument("--experiment", required=True, help="Experiment ID (E1-E5)")
    parser.add_argument(
        "--participants", type=int, default=20, help="Number of participants"
    )
    args = parser.parse_args()

    asyncio.run(main(args.experiment, args.participants))
