"""
NeuroSync AI — M12: Circadian optimizer.

Identifies the student's peak cognitive hours by correlating quiz
performance with time-of-day and returns a ``CognitiveProfile``.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Optional

import numpy as np
from loguru import logger
from pydantic import BaseModel

from neurosync.config.settings import SPACED_REPETITION_CONFIG as CFG
from neurosync.database.manager import DatabaseManager


class CognitiveProfile(BaseModel):
    """Student's peak-performance window."""

    student_id: str
    peak_start_hour: float
    peak_end_hour: float
    confidence: Literal["low", "medium", "high"] = "low"
    data_points: int = 0
    mean_peak_performance: Optional[float] = None


class CircadianOptimizer:
    """Identifies cognitive-peak hours and optimizes review timing."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ------------------------------------------------------------------
    def get_cognitive_peak(self, student_id: str) -> CognitiveProfile:
        """
        Analyse quiz scores by time-of-day.

        Returns a 3-hour window with the highest average performance.
        Needs ≥ 20 sessions to produce a ``"medium"`` or ``"high"``
        confidence result.
        """
        min_sessions = int(CFG["CIRCADIAN_MIN_SESSIONS"])
        default_start = float(CFG["CIRCADIAN_DEFAULT_PEAK_START"])
        default_end = float(CFG["CIRCADIAN_DEFAULT_PEAK_END"])
        window_h = int(CFG["CIRCADIAN_WINDOW_HOURS"])

        rows = self._db.fetch_all(
            "SELECT start_time_of_day, quiz_score_percentage "
            "FROM session_summaries "
            "WHERE student_id = ? AND quiz_score_percentage IS NOT NULL",
            (student_id,),
        )

        if len(rows) < min_sessions:
            return CognitiveProfile(
                student_id=student_id,
                peak_start_hour=default_start,
                peak_end_hour=default_end,
                confidence="low",
                data_points=len(rows),
            )

        # Group scores by hour
        by_hour: dict[int, list[float]] = {}
        for row in rows:
            # start_time_of_day is stored as fractional hour
            hour = int(row["start_time_of_day"]) if row["start_time_of_day"] is not None else 12
            by_hour.setdefault(hour, []).append(float(row["quiz_score_percentage"]))

        mean_by_hour: dict[int, float] = {
            h: float(np.mean(scores))
            for h, scores in by_hour.items()
            if len(scores) >= 3
        }

        if not mean_by_hour:
            return CognitiveProfile(
                student_id=student_id,
                peak_start_hour=default_start,
                peak_end_hour=default_end,
                confidence="low",
                data_points=len(rows),
            )

        best_start: int = int(default_start)
        best_score: float = 0.0
        for start in range(6, 22):
            window_scores = [
                mean_by_hour[h]
                for h in range(start, start + window_h)
                if h in mean_by_hour
            ]
            if not window_scores:
                continue
            avg = float(np.mean(window_scores))
            if avg > best_score:
                best_score = avg
                best_start = start

        confidence: Literal["low", "medium", "high"] = (
            "high" if len(rows) >= 50 else "medium"
        )

        return CognitiveProfile(
            student_id=student_id,
            peak_start_hour=float(best_start),
            peak_end_hour=float(best_start + window_h),
            confidence=confidence,
            data_points=len(rows),
            mean_peak_performance=best_score,
        )

    # ------------------------------------------------------------------
    def optimize_review_time(
        self,
        student_id: str,
        target_date: datetime | None = None,
    ) -> float:
        """
        Return a timestamp in the middle of the cognitive-peak window
        on *target_date*.
        """
        if target_date is None:
            target_date = datetime.now()

        profile = self.get_cognitive_peak(student_id)
        optimal_hour = (profile.peak_start_hour + profile.peak_end_hour) / 2.0

        dt = datetime.combine(
            target_date.date() if isinstance(target_date, datetime) else target_date,
            datetime.min.time(),
        ) + timedelta(hours=optimal_hour)

        return dt.timestamp()
