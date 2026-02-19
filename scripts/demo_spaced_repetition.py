#!/usr/bin/env python
"""
NeuroSync AI — 30-day spaced-repetition simulation.

Demonstrates personalised forgetting curves, adaptive scheduling,
and compares NeuroSync efficiency against fixed-interval (Anki).

Usage:
    python scripts/demo_spaced_repetition.py
"""

from __future__ import annotations

import random
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

from neurosync.database.manager import DatabaseManager
from neurosync.spaced_repetition.analytics import SpacedRepetitionAnalytics
from neurosync.spaced_repetition.forgetting_curve.fitter import ForgettingCurveFitter
from neurosync.spaced_repetition.forgetting_curve.models import RetentionPoint
from neurosync.spaced_repetition.forgetting_curve.predictor import RetentionPredictor
from neurosync.spaced_repetition.scheduler import SpacedRepetitionScheduler

STUDENT = "Arjun"
CONCEPTS = ["photosynthesis", "osmosis", "mitosis", "respiration", "cell_division"]

# Simulated "true" decay constants per concept (hidden from algorithm)
TRUE_TAU: dict[str, float] = {
    "photosynthesis": 4.2,
    "osmosis": 3.0,
    "mitosis": 5.5,
    "respiration": 2.8,
    "cell_division": 6.0,
}


def _simulate_score(concept: str, hours_since_mastery: float) -> float:
    """Produce a noisy score based on the true forgetting curve."""
    import math

    tau = TRUE_TAU[concept]
    days = hours_since_mastery / 24.0
    retention = 0.95 * math.exp(-days / tau)
    noise = random.gauss(0, 0.03)
    return max(0, min(100, (retention + noise) * 100))


def main() -> None:
    print("=" * 55)
    print("     30-DAY LEARNING SIMULATION  —  NeuroSync AI")
    print("=" * 55)
    print(f"Student: {STUDENT}")
    print(f"Concepts to master: {len(CONCEPTS)} ({', '.join(CONCEPTS)})\n")

    # Set up temp database
    tmp = Path(tempfile.mkdtemp()) / "demo.db"
    db = DatabaseManager(tmp)
    db.initialise()

    scheduler = SpacedRepetitionScheduler(db=db)
    analytics = SpacedRepetitionAnalytics(db=db)
    predictor = RetentionPredictor()
    fitter = ForgettingCurveFitter()

    # Simulation clock (epoch seconds)
    now = time.time()
    sim_start = now

    # Day 1 — master all concepts
    print("DAY 1:")
    for concept in CONCEPTS:
        score = random.uniform(90, 98)
        scheduler.record_mastery(STUDENT, concept, score, now)
        print(f"  Mastered: {concept} (score: {score:.0f}%)")
    print(f"  First reviews scheduled: 2 h from now\n")

    # Simulate 30 days
    total_reviews = 0
    day_offset = 0

    while day_offset <= 30:
        sim_time = sim_start + (day_offset * 86400)

        due = scheduler.get_due_reviews(STUDENT, current_time=sim_time)
        if due:
            day_str = f"DAY {day_offset}" if day_offset > 0 else "DAY 1 (+2h)"
            print(f"{day_str}:")
            for review in due:
                concept = review.concept_id
                hours = (sim_time - (sim_start - 86400)) / 3600  # approx
                score = _simulate_score(concept, hours)
                curve = scheduler.record_review(STUDENT, concept, score, sim_time)
                total_reviews += 1
                print(
                    f"  Review {review.review_number}: {concept} "
                    f"(score: {score:.0f}%) "
                    f"τ={curve.tau_days:.1f}d R²={curve.confidence:.2f}"
                )
            print()

        # Advance by 0.5-2 days (varying intervals)
        day_offset += random.choice([0.5, 1, 1, 2])

    # Final stats
    stats = analytics.get_retention_stats(STUDENT)
    comparison = analytics.compare_with_anki(STUDENT)

    print("=" * 55)
    print("FINAL STATISTICS:")
    print(f"  Total concepts mastered: {stats.total_concepts}")
    print(f"  Total reviews completed: {stats.total_reviews}")
    print(f"  Average retention at 30 days: {stats.average_retention * 100:.1f}%")
    print()
    print("Comparison to Anki (fixed intervals):")
    print(f"  NeuroSync: {comparison['neurosync']['retention']*100:.1f}% retention, "
          f"{comparison['neurosync']['reviews']} reviews")
    print(f"  Anki:      {comparison['anki']['retention']*100:.1f}% retention, "
          f"{comparison['anki']['reviews']} reviews")
    print()
    print(f"  NeuroSync efficiency: {comparison['efficiency_gain_percent']}% better retention "
          f"with {comparison['fewer_reviews_percent']}% fewer reviews ✓")
    print("=" * 55)

    db.close()


if __name__ == "__main__":
    main()
