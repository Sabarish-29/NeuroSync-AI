"""
Step 8 — Circadian optimizer tests (4 tests).
"""

from __future__ import annotations

import time
from datetime import datetime

import pytest

from neurosync.database.manager import DatabaseManager
from neurosync.spaced_repetition.timing.circadian_optimizer import (
    CircadianOptimizer,
    CognitiveProfile,
)


def _seed_sessions(db: DatabaseManager, n: int, peak_hour: int = 15) -> None:
    """Insert *n* session_summaries with quiz scores peaking at *peak_hour*."""
    import time as _t
    now = _t.time()
    for i in range(n):
        hour = 8 + (i % 14)  # 8 AM - 9 PM cycle
        score = 85.0 if abs(hour - peak_hour) <= 1 else 60.0
        sid = f"sess_{i}"
        # Parent row required by FK constraint
        db.execute(
            "INSERT OR IGNORE INTO sessions "
            "(session_id, student_id, lesson_id, started_at) "
            "VALUES (?, ?, ?, ?)",
            (sid, "stu1", "L1", now - i * 86400),
        )
        db.execute(
            "INSERT INTO session_summaries "
            "(summary_id, session_id, student_id, lesson_id, "
            " start_time_of_day, quiz_score_percentage) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (f"sum_{i}", sid, "stu1", "L1", float(hour), score),
        )


class TestCircadianOptimizer:

    def test_cognitive_peak_identified_from_performance(self, sr_db: DatabaseManager):
        """Peak window centres around the highest-scoring hours."""
        _seed_sessions(sr_db, 60, peak_hour=15)
        opt = CircadianOptimizer(sr_db)
        profile = opt.get_cognitive_peak("stu1")
        # Peak should include hour 15
        assert profile.peak_start_hour <= 15 <= profile.peak_end_hour

    def test_peak_window_is_3_hours(self, sr_db: DatabaseManager):
        """The window should always span exactly 3 hours."""
        _seed_sessions(sr_db, 60, peak_hour=10)
        opt = CircadianOptimizer(sr_db)
        profile = opt.get_cognitive_peak("stu1")
        assert profile.peak_end_hour - profile.peak_start_hour == 3

    def test_insufficient_data_returns_default(self, sr_db: DatabaseManager):
        """< 20 sessions → default 14-17 window, low confidence."""
        _seed_sessions(sr_db, 5)
        opt = CircadianOptimizer(sr_db)
        profile = opt.get_cognitive_peak("stu1")
        assert profile.confidence == "low"
        assert profile.peak_start_hour == 14.0
        assert profile.peak_end_hour == 17.0

    def test_optimize_review_time_targets_peak(self, sr_db: DatabaseManager):
        """optimize_review_time should return a mid-peak timestamp."""
        _seed_sessions(sr_db, 60, peak_hour=15)
        opt = CircadianOptimizer(sr_db)
        ts = opt.optimize_review_time("stu1")
        dt = datetime.fromtimestamp(ts)
        # Should be in the afternoon
        assert 12 <= dt.hour <= 20
