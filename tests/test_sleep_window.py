"""
Step 8 — Sleep-window tests (3 tests).
"""

from __future__ import annotations

import time
from datetime import datetime

import pytest

from neurosync.database.manager import DatabaseManager
from neurosync.spaced_repetition.timing.sleep_window import SleepWindowDetector


class TestSleepWindow:

    def test_estimate_bedtime_from_session_history(self, sr_db: DatabaseManager):
        """With enough session-end data, bedtime should be estimated."""
        # Seed 5 sessions ending around 22:00-23:00
        now = time.time()
        for i in range(5):
            sid = f"sess_{i}"
            # ended_at ≈ 22:30 local
            dt = datetime.now().replace(hour=22, minute=30, second=0)
            ended_at = dt.timestamp() - (i * 86400)
            sr_db.execute(
                "INSERT INTO sessions (session_id, student_id, lesson_id, started_at, ended_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (sid, "stu1", "lesson", ended_at - 3600, ended_at),
            )

        detector = SleepWindowDetector(sr_db)
        bedtime = detector.estimate_bedtime("stu1")
        # Should be ≈ 22.5 ± 1 h
        assert 21.0 <= bedtime <= 24.0

    def test_sleep_window_60_min_before_bedtime(self, sr_db: DatabaseManager):
        """Consolidation window should start 60 min before bedtime."""
        detector = SleepWindowDetector(sr_db)
        # No sessions → default bedtime = 22.0
        bedtime = detector.estimate_bedtime("nobody")
        assert bedtime == 22.0

        start_ts = detector.get_sleep_window_start("nobody")
        start_dt = datetime.fromtimestamp(start_ts)
        assert start_dt.hour == 21  # 22:00 - 1h = 21:00

    def test_hard_concepts_scheduled_in_sleep_window(self):
        """Mastery 60-85 % should be eligible for sleep-window review."""
        assert SleepWindowDetector.should_schedule_in_sleep_window(0.70) is True
        assert SleepWindowDetector.should_schedule_in_sleep_window(0.50) is False
        assert SleepWindowDetector.should_schedule_in_sleep_window(0.90) is False
