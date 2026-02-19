"""
NeuroSync AI — Daily review-session planner.

Combines the sleep-window detector, circadian optimizer, and the
list of due reviews into a single ordered schedule for the day.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from neurosync.database.manager import DatabaseManager
from neurosync.spaced_repetition.timing.circadian_optimizer import CircadianOptimizer
from neurosync.spaced_repetition.timing.sleep_window import SleepWindowDetector


class PlannedReview(BaseModel):
    """Single item inside the daily plan."""

    concept_id: str
    scheduled_at: float
    review_number: int = 1
    predicted_retention: float = 0.0
    slot: str = "peak"  # "peak" | "sleep_window"


class DailyPlan(BaseModel):
    """Full review plan for one day."""

    date: str = ""
    total_reviews: int = 0
    reviews: list[PlannedReview] = Field(default_factory=list)
    estimated_duration_minutes: int = 0


class SessionPlanner:
    """Builds an optimised daily review schedule."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db
        self._circadian = CircadianOptimizer(db)
        self._sleep = SleepWindowDetector(db)

    def build_daily_plan(
        self,
        student_id: str,
        due_concept_ids: list[str],
        target_date: datetime | None = None,
    ) -> DailyPlan:
        if target_date is None:
            target_date = datetime.now()

        peak_ts = self._circadian.optimize_review_time(student_id, target_date)
        sleep_ts = self._sleep.get_sleep_window_start(student_id, target_date)

        reviews: list[PlannedReview] = []
        for cid in due_concept_ids:
            reviews.append(
                PlannedReview(
                    concept_id=cid,
                    scheduled_at=peak_ts,
                    slot="peak",
                )
            )

        return DailyPlan(
            date=target_date.strftime("%Y-%m-%d"),
            total_reviews=len(reviews),
            reviews=reviews,
            estimated_duration_minutes=len(reviews) * 3,
        )
