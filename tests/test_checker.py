"""Tests for the readiness checker / orchestrator (Step 9)."""

import time

from neurosync.readiness.assessments.behavioral import WarmupAnswer
from neurosync.readiness.checker import run_check, recheck_after_intervention
from neurosync.database.manager import DatabaseManager


def _insert_session(db: DatabaseManager, session_id: str, student_id: str) -> None:
    """Insert a parent session row so FK constraints pass."""
    db.execute(
        "INSERT INTO sessions (session_id, student_id, lesson_id, started_at) VALUES (?, ?, ?, ?)",
        (session_id, student_id, "lesson_test", time.time()),
    )


class TestChecker:
    """End-to-end readiness checker tests."""

    def test_full_check(self, db_manager: DatabaseManager) -> None:
        """Full check with all inputs persists to the database."""
        _insert_session(db_manager, "sess_001", "stu_001")
        result = run_check(
            session_id="sess_001",
            student_id="stu_001",
            lesson_topic="Fractions",
            self_report_responses={
                "familiarity": 3,
                "difficulty_perception": 3,
                "emotional_state": 3,
            },
            blink_rate=16.0,
            warmup_answers=[
                WarmupAnswer(question_id="q1", correct=True, response_time_seconds=7.0),
            ],
            db=db_manager,
        )
        assert result.readiness_score > 0
        assert result.status in ("ready", "not_ready", "needs_intervention")

        # Verify persistence
        row = db_manager.fetch_one(
            "SELECT * FROM readiness_checks WHERE check_id = ?",
            (result.check_id,),
        )
        assert row is not None

    def test_recheck_after_intervention(self, db_manager: DatabaseManager) -> None:
        """Recheck after breathing should carry forward metadata."""
        _insert_session(db_manager, "sess_002", "stu_002")
        initial = run_check(
            session_id="sess_002",
            student_id="stu_002",
            lesson_topic="Algebra",
            self_report_responses={
                "familiarity": 1,
                "difficulty_perception": 5,
                "emotional_state": 5,
            },
            blink_rate=30.0,
            db=db_manager,
        )
        # Simulate post-breathing improvement
        updated = recheck_after_intervention(
            initial,
            self_report_responses={
                "familiarity": 2,
                "difficulty_perception": 3,
                "emotional_state": 2,
            },
            blink_rate=18.0,
            breathing_completed=True,
            db=db_manager,
        )
        assert updated.breathing_completed is True
        # Anxiety should be lower after the "improvement"
        assert updated.anxiety_score < initial.anxiety_score
