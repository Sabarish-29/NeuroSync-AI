"""
Step 8 — Scheduler tests (6 tests).
"""

from __future__ import annotations

import time

import pytest

from neurosync.database.manager import DatabaseManager
from neurosync.spaced_repetition.scheduler import SpacedRepetitionScheduler


class TestScheduler:

    def test_record_mastery_schedules_first_review(self, scheduler: SpacedRepetitionScheduler, sr_db: DatabaseManager):
        """After mastery, a scheduled_reviews row should exist."""
        now = time.time()
        scheduler.record_mastery("stu1", "photosynthesis", 95, now)

        row = sr_db.fetch_one(
            "SELECT * FROM scheduled_reviews WHERE student_id = ? AND concept_id = ?",
            ("stu1", "photosynthesis"),
        )
        assert row is not None
        assert row["review_number"] == 1
        assert row["review_at"] > now

    def test_record_review_updates_curve(self, scheduler: SpacedRepetitionScheduler, sr_db: DatabaseManager):
        """Recording a review should produce a forgetting_curves row."""
        now = time.time()
        scheduler.record_mastery("stu1", "osmosis", 95, now - 86400)
        # Simulate 24h-later review
        curve = scheduler.record_review("stu1", "osmosis", 82, now)
        assert curve.tau_days > 0

        fc_row = sr_db.fetch_one(
            "SELECT * FROM forgetting_curves WHERE student_id = ? AND concept_id = ?",
            ("stu1", "osmosis"),
        )
        assert fc_row is not None
        assert fc_row["tau_days"] > 0

    def test_get_due_reviews_returns_overdue(self, scheduler: SpacedRepetitionScheduler):
        """Reviews scheduled in the past should be returned."""
        past = time.time() - 86400
        scheduler.record_mastery("stu1", "mitosis", 90, past - 86400)
        # The first review is 2 h after mastery → already past
        due = scheduler.get_due_reviews("stu1", current_time=time.time())
        concepts = [d.concept_id for d in due]
        assert "mitosis" in concepts

    def test_review_difficulty_adapts_by_number(self, scheduler: SpacedRepetitionScheduler):
        """Quiz difficulty should escalate with review number."""
        from neurosync.spaced_repetition.quiz.difficulty_adapter import DifficultyAdapter
        da = DifficultyAdapter()
        assert da.determine_difficulty(1) == "easy"
        assert da.determine_difficulty(2) == "medium"
        assert da.determine_difficulty(3) == "hard"

    def test_multiple_concepts_tracked_independently(self, scheduler: SpacedRepetitionScheduler, sr_db: DatabaseManager):
        """Two concepts get separate mastery rows."""
        now = time.time()
        scheduler.record_mastery("stu1", "concept_a", 90, now)
        scheduler.record_mastery("stu1", "concept_b", 88, now)

        rows = sr_db.fetch_all(
            "SELECT concept_id FROM mastery_records WHERE student_id = 'stu1'",
        )
        ids = {r["concept_id"] for r in rows}
        assert ids == {"concept_a", "concept_b"}

    def test_scheduler_handles_no_due_reviews(self, scheduler: SpacedRepetitionScheduler):
        """Empty DB → empty list, no crash."""
        due = scheduler.get_due_reviews("nobody")
        assert due == []
