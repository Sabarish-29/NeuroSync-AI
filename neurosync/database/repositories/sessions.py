"""
NeuroSync AI — Session repository.

CRUD operations for the sessions table.
"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from neurosync.core.events import SessionConfig
from neurosync.database.manager import DatabaseManager


class SessionRepository:
    """Repository for session records."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def create_session(self, config: SessionConfig) -> str:
        """Create a new session record. Returns session_id."""
        self._db.execute(
            """INSERT INTO sessions
               (session_id, student_id, lesson_id, started_at,
                eeg_enabled, webcam_enabled, experiment_group)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                config.session_id,
                config.student_id,
                config.lesson_id,
                config.started_at,
                int(config.eeg_enabled),
                int(config.webcam_enabled),
                config.experiment_group,
            ),
        )
        logger.info("Session created: {}", config.session_id)
        return config.session_id

    def end_session(
        self,
        session_id: str,
        ended_at: float,
        total_duration_ms: float,
        completion_percentage: float,
    ) -> None:
        """Mark a session as ended."""
        self._db.execute(
            """UPDATE sessions
               SET ended_at = ?, total_duration_ms = ?, completion_percentage = ?
               WHERE session_id = ?""",
            (ended_at, total_duration_ms, completion_percentage, session_id),
        )
        logger.info("Session ended: {}", session_id)

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a session by ID."""
        row = self._db.fetch_one(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        if row is None:
            return None
        return dict(row)

    def get_student_sessions(self, student_id: str) -> list[dict[str, Any]]:
        """Get all sessions for a student."""
        rows = self._db.fetch_all(
            "SELECT * FROM sessions WHERE student_id = ? ORDER BY started_at DESC",
            (student_id,),
        )
        return [dict(r) for r in rows]
