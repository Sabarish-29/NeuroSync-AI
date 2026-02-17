"""
NeuroSync AI — Event repository.

Handles logging raw events to the database.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

from neurosync.core.events import QuestionEvent, RawEvent
from neurosync.database.manager import DatabaseManager


class EventRepository:
    """Repository for raw event records."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def insert_event(self, event: RawEvent) -> None:
        """Insert a raw event."""
        self._db.execute(
            """INSERT INTO events
               (event_id, session_id, student_id, timestamp, event_type, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                event.event_id,
                event.session_id,
                event.student_id,
                event.timestamp,
                event.event_type,
                json.dumps(event.metadata, default=str),
            ),
        )
        logger.debug("Event logged: {} ({})", event.event_type, event.event_id)

    def insert_question_attempt(self, event: QuestionEvent, authenticity_score: float = 0.0, mastery_flag: str = "accept") -> None:
        """Insert a question attempt record."""
        attempt_id = DatabaseManager.generate_id()
        self._db.execute(
            """INSERT INTO question_attempts
               (attempt_id, session_id, student_id, question_id, concept_id,
                timestamp, answer_given, answer_correct, response_time_ms,
                confidence_score, attempt_number, authenticity_score, mastery_flag)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                attempt_id,
                event.session_id,
                event.student_id,
                event.question_id,
                event.concept_id,
                event.timestamp,
                event.answer_given,
                int(event.answer_correct) if event.answer_correct is not None else None,
                event.response_time_ms,
                event.confidence_score,
                event.attempt_number,
                authenticity_score,
                mastery_flag,
            ),
        )
        logger.debug("Question attempt logged: {}", event.question_id)

    def get_session_events(
        self, session_id: str, event_type: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Get all events for a session, optionally filtered by type."""
        if event_type:
            rows = self._db.fetch_all(
                "SELECT * FROM events WHERE session_id = ? AND event_type = ? ORDER BY timestamp",
                (session_id, event_type),
            )
        else:
            rows = self._db.fetch_all(
                "SELECT * FROM events WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            )
        return [dict(r) for r in rows]

    def get_event_count(self, session_id: str) -> int:
        """Get total number of events in a session."""
        row = self._db.fetch_one(
            "SELECT COUNT(*) as cnt FROM events WHERE session_id = ?",
            (session_id,),
        )
        return int(row["cnt"]) if row else 0
