"""
NeuroSync AI — Tests for the database layer.

Tests:
  21. test_event_write_read — write event, read it back correctly
  22. test_session_create — session created with all fields
  23. test_snapshot_write — signal snapshot written correctly
  24. test_concurrent_writes — multiple writers don't corrupt data
  25. test_mastery_record_upsert — upsert works correctly
"""

import threading
import time

import pytest

from neurosync.core.events import InterventionRequest, RawEvent, SessionConfig
from neurosync.database.manager import DatabaseManager
from neurosync.database.repositories.events import EventRepository
from neurosync.database.repositories.sessions import SessionRepository
from neurosync.database.repositories.signals import SignalRepository
from tests.conftest import make_raw_event


class TestEventRepository:
    """Tests for event read/write."""

    def test_event_write_read(self, db_manager: DatabaseManager) -> None:
        """Write an event, then read it back and verify all fields."""
        # Create session first (FK constraint)
        session_repo = SessionRepository(db_manager)
        config = SessionConfig(student_id="test_student", lesson_id="test_lesson")
        session_repo.create_session(config)

        event_repo = EventRepository(db_manager)
        event = make_raw_event(
            session_id=config.session_id,
            student_id="test_student",
            event_type="click",
        )
        event_repo.insert_event(event)

        # Read back
        events = event_repo.get_session_events(config.session_id)
        assert len(events) == 1
        assert events[0]["event_id"] == event.event_id
        assert events[0]["event_type"] == "click"
        assert events[0]["student_id"] == "test_student"

    def test_event_count(self, db_manager: DatabaseManager) -> None:
        """Event count is accurate."""
        session_repo = SessionRepository(db_manager)
        config = SessionConfig(student_id="test_student", lesson_id="test_lesson")
        session_repo.create_session(config)

        event_repo = EventRepository(db_manager)
        for i in range(5):
            event_repo.insert_event(make_raw_event(
                session_id=config.session_id,
                student_id="test_student",
            ))

        assert event_repo.get_event_count(config.session_id) == 5

    def test_event_filter_by_type(self, db_manager: DatabaseManager) -> None:
        """Events can be filtered by type."""
        session_repo = SessionRepository(db_manager)
        config = SessionConfig(student_id="test_student", lesson_id="test_lesson")
        session_repo.create_session(config)

        event_repo = EventRepository(db_manager)
        event_repo.insert_event(make_raw_event(session_id=config.session_id, event_type="click"))
        event_repo.insert_event(make_raw_event(session_id=config.session_id, event_type="scroll"))
        event_repo.insert_event(make_raw_event(session_id=config.session_id, event_type="click"))

        clicks = event_repo.get_session_events(config.session_id, event_type="click")
        assert len(clicks) == 2


class TestSessionRepository:
    """Tests for session CRUD."""

    def test_session_create(self, db_manager: DatabaseManager) -> None:
        """Session is created with all fields."""
        repo = SessionRepository(db_manager)
        config = SessionConfig(
            student_id="student_123",
            lesson_id="lesson_456",
            eeg_enabled=True,
            webcam_enabled=False,
            experiment_group="treatment",
        )
        session_id = repo.create_session(config)

        session = repo.get_session(session_id)
        assert session is not None
        assert session["student_id"] == "student_123"
        assert session["lesson_id"] == "lesson_456"
        assert session["eeg_enabled"] == 1
        assert session["webcam_enabled"] == 0
        assert session["experiment_group"] == "treatment"

    def test_session_end(self, db_manager: DatabaseManager) -> None:
        """Session end updates correctly."""
        repo = SessionRepository(db_manager)
        config = SessionConfig(student_id="student", lesson_id="lesson")
        session_id = repo.create_session(config)

        repo.end_session(
            session_id=session_id,
            ended_at=config.started_at + 1800000,  # 30 minutes
            total_duration_ms=1800000,
            completion_percentage=85.0,
        )

        session = repo.get_session(session_id)
        assert session is not None
        assert session["total_duration_ms"] == 1800000
        assert session["completion_percentage"] == 85.0


class TestSignalRepository:
    """Tests for signal snapshots and mastery records."""

    def test_snapshot_write(self, db_manager: DatabaseManager) -> None:
        """Signal snapshot is written and can be retrieved."""
        session_repo = SessionRepository(db_manager)
        config = SessionConfig(student_id="student", lesson_id="lesson")
        session_repo.create_session(config)

        signal_repo = SignalRepository(db_manager)
        snapshot_id = signal_repo.insert_snapshot(
            session_id=config.session_id,
            timestamp=time.time() * 1000,
            frustration_score=0.65,
            fatigue_score=0.3,
            response_time_mean_ms=7500.0,
            active_moments=["M07"],
        )

        snapshots = signal_repo.get_session_snapshots(config.session_id)
        assert len(snapshots) == 1
        assert snapshots[0]["frustration_score"] == pytest.approx(0.65)
        assert snapshots[0]["fatigue_score"] == pytest.approx(0.3)

    def test_mastery_record_upsert(self, db_manager: DatabaseManager) -> None:
        """Mastery upsert creates then updates correctly."""
        signal_repo = SignalRepository(db_manager)

        # First insert
        signal_repo.upsert_mastery(
            student_id="student_1",
            concept_id="concept_1",
            authenticity_score=0.45,
            timestamp=1000.0,
        )

        record = signal_repo.get_mastery("student_1", "concept_1")
        assert record is not None
        assert record["authenticity_score"] == pytest.approx(0.45)
        assert record["review_count"] == 1

        # Upsert (update)
        signal_repo.upsert_mastery(
            student_id="student_1",
            concept_id="concept_1",
            authenticity_score=0.85,
            timestamp=2000.0,
        )

        record = signal_repo.get_mastery("student_1", "concept_1")
        assert record is not None
        assert record["authenticity_score"] == pytest.approx(0.85)
        assert record["review_count"] == 2


class TestConcurrentWrites:
    """Test thread safety of database operations."""

    def test_concurrent_writes(self, db_manager: DatabaseManager) -> None:
        """Multiple threads writing events simultaneously don't corrupt data."""
        session_repo = SessionRepository(db_manager)
        config = SessionConfig(student_id="student", lesson_id="lesson")
        session_repo.create_session(config)

        event_repo = EventRepository(db_manager)
        errors: list[Exception] = []
        events_per_thread = 20
        thread_count = 4

        def write_events(thread_id: int) -> None:
            try:
                for i in range(events_per_thread):
                    event_repo.insert_event(make_raw_event(
                        session_id=config.session_id,
                        student_id=f"thread_{thread_id}",
                    ))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=write_events, args=(t,))
            for t in range(thread_count)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent write errors: {errors}"
        total = event_repo.get_event_count(config.session_id)
        assert total == events_per_thread * thread_count
