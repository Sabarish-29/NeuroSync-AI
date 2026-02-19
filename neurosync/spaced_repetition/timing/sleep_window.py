"""
NeuroSync AI — M19: Sleep-window scheduling.

Detects the student's typical bedtime from session-end history and
returns a "consolidation window" 60 minutes before bedtime so that
hard / weakly-encoded concepts can be reviewed right before sleep.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from loguru import logger

from neurosync.config.settings import SPACED_REPETITION_CONFIG as CFG
from neurosync.database.manager import DatabaseManager


class SleepWindowDetector:
    """Detects bedtime and returns the pre-sleep consolidation window."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ------------------------------------------------------------------
    def estimate_bedtime(self, student_id: str) -> float:
        """
        Estimate the student's typical bedtime (hour of day, 0.0-24.0).

        Uses the 90th-percentile of session-end times from the last 14
        days.  Falls back to ``DEFAULT_BEDTIME_HOUR`` when insufficient
        data.
        """
        window_days = int(CFG["SLEEP_OBSERVATION_WINDOW_DAYS"])
        import time as _time

        cutoff = _time.time() - (window_days * 86400)

        rows = self._db.fetch_all(
            "SELECT ended_at FROM sessions "
            "WHERE student_id = ? AND ended_at IS NOT NULL AND ended_at > ? "
            "ORDER BY ended_at DESC",
            (student_id, cutoff),
        )

        if len(rows) < 3:
            return float(CFG["DEFAULT_BEDTIME_HOUR"])

        end_hours: list[float] = []
        for row in rows:
            dt = datetime.fromtimestamp(row["ended_at"])
            end_hours.append(dt.hour + dt.minute / 60.0)

        bedtime = float(np.percentile(end_hours, 90))
        logger.info("Estimated bedtime for {}: {:02.0f}:{:02.0f}", student_id, int(bedtime), int((bedtime % 1) * 60))
        return bedtime

    # ------------------------------------------------------------------
    def get_sleep_window_start(
        self,
        student_id: str,
        target_date: datetime | None = None,
    ) -> float:
        """
        Return the **timestamp** of the consolidation-window start
        (60 min before bedtime) on *target_date*.
        """
        if target_date is None:
            target_date = datetime.now()

        bedtime_hour = self.estimate_bedtime(student_id)
        minutes_before = float(CFG["SLEEP_WINDOW_MINUTES_BEFORE"])
        window_start_hour = bedtime_hour - (minutes_before / 60.0)

        dt = datetime.combine(
            target_date.date() if isinstance(target_date, datetime) else target_date,
            datetime.min.time(),
        ) + timedelta(hours=window_start_hour)

        return dt.timestamp()

    # ------------------------------------------------------------------
    @staticmethod
    def should_schedule_in_sleep_window(mastery_score: float) -> bool:
        """
        Hard / weakly-encoded concepts (mastery 60-85 %) benefit most
        from pre-sleep consolidation.
        """
        low = float(CFG["SLEEP_MASTERY_LOW"])
        high = float(CFG["SLEEP_MASTERY_HIGH"])
        return low <= mastery_score <= high
