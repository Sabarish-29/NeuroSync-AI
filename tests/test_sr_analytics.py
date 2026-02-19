"""
Step 8 — Analytics tests (1 test).
"""

from __future__ import annotations

import time

import pytest

from neurosync.database.manager import DatabaseManager
from neurosync.spaced_repetition.analytics import SpacedRepetitionAnalytics
from neurosync.spaced_repetition.scheduler import SpacedRepetitionScheduler


class TestAnalytics:

    def test_retention_rate_tracking_across_reviews(
        self, scheduler: SpacedRepetitionScheduler, sr_db: DatabaseManager,
    ):
        """After mastery + review, analytics should report > 0 retention."""
        now = time.time()
        scheduler.record_mastery("stu1", "cell_division", 95, now - 172800)
        scheduler.record_review("stu1", "cell_division", 80, now - 86400)
        scheduler.record_review("stu1", "cell_division", 78, now)

        analytics = SpacedRepetitionAnalytics(sr_db)
        stats = analytics.get_retention_stats("stu1")

        assert stats.total_concepts == 1
        assert stats.total_reviews >= 2
        assert stats.average_retention > 0
