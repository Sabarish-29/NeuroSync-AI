"""
NeuroSync AI — Async event collector.

Receives events from the frontend (later from Electron via IPC, for now via
direct Python calls). Stores events to SQLite and dispatches them to signal
processors in real time.

Flow: Event arrives → validate (Pydantic) → write to SQLite →
      push to asyncio.Queue → signal processors consume from queue
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

from loguru import logger

from neurosync.core.events import (
    IdleEvent,
    QuestionEvent,
    RawEvent,
    SessionConfig,
    VideoEvent,
)
from neurosync.database.manager import DatabaseManager
from neurosync.database.repositories.events import EventRepository
from neurosync.database.repositories.sessions import SessionRepository

# Step 2 — optional webcam score type (imported lazily to avoid hard dep)
try:
    from neurosync.webcam.fusion import WebcamMomentScores as _WebcamScores
except ImportError:  # pragma: no cover
    _WebcamScores = None  # type: ignore[assignment,misc]


class AsyncEventCollector:
    """
    Async event collector that validates, persists, and dispatches events.

    All events are pushed to an asyncio.Queue for downstream signal processors.
    """

    def __init__(self, session_config: SessionConfig, db_manager: DatabaseManager) -> None:
        self._config = session_config
        self._db = db_manager
        self._event_repo = EventRepository(db_manager)
        self._session_repo = SessionRepository(db_manager)
        self._queue: asyncio.Queue[RawEvent] = asyncio.Queue()
        self._event_count = 0
        self._question_count = 0
        self._correct_count = 0
        self._rewind_count = 0
        self._started = False
        logger.info("AsyncEventCollector initialised for session {}", session_config.session_id)

    async def start(self) -> None:
        """Start the collector — creates the session record."""
        if not self._started:
            self._session_repo.create_session(self._config)
            self._started = True
            logger.info("Collector started for session {}", self._config.session_id)

    @property
    def queue(self) -> asyncio.Queue[RawEvent]:
        """Access the event queue for downstream consumers."""
        return self._queue

    @property
    def event_count(self) -> int:
        return self._event_count

    async def record_event(self, event: RawEvent) -> None:
        """Validate, persist, and dispatch a raw event."""
        # Ensure session_id matches
        event.session_id = self._config.session_id
        event.student_id = self._config.student_id

        # Persist to database
        self._event_repo.insert_event(event)
        self._event_count += 1

        # Push to queue for signal processors
        await self._queue.put(event)
        logger.debug("Event recorded: {} (total: {})", event.event_type, self._event_count)

    async def record_question(self, event: QuestionEvent) -> None:
        """Specialized handler for question events."""
        event.session_id = self._config.session_id
        event.student_id = self._config.student_id

        self._event_repo.insert_event(event)
        self._event_count += 1
        self._question_count += 1
        if event.answer_correct:
            self._correct_count += 1

        await self._queue.put(event)
        logger.debug(
            "Question recorded: {} (correct: {}, response_time: {}ms)",
            event.question_id,
            event.answer_correct,
            event.response_time_ms,
        )

    async def record_video(self, event: VideoEvent) -> None:
        """Specialized handler for video events — counts rewinds, seeks."""
        event.session_id = self._config.session_id
        event.student_id = self._config.student_id

        if event.event_type == "video_rewind":
            self._rewind_count += 1

        self._event_repo.insert_event(event)
        self._event_count += 1

        await self._queue.put(event)
        logger.debug("Video event: {} at {}ms", event.event_type, event.playback_position_ms)

    async def record_idle(self, event: IdleEvent) -> None:
        """Specialized handler for idle events."""
        event.session_id = self._config.session_id
        event.student_id = self._config.student_id

        self._event_repo.insert_event(event)
        self._event_count += 1

        await self._queue.put(event)
        logger.debug("Idle event: {}ms after {}", event.idle_duration_ms, event.preceding_event_type)

    # ------------------------------------------------------------------
    # Step 2 — Webcam signal injection
    # ------------------------------------------------------------------

    async def inject_webcam_signal(self, scores: object) -> None:
        """
        Merge webcam moment scores into the current signal context.

        Called by ``WebcamSignalInjector`` so that the behavioral fusion
        engine can use visual signals in its next cycle.

        Parameters
        ----------
        scores:
            A ``WebcamMomentScores`` instance (from ``neurosync.webcam.fusion``).
        """
        # Store latest webcam scores for downstream consumers
        self._latest_webcam_scores = scores
        logger.debug(
            "Webcam signal injected — face_detected={}, attention={:.2f}",
            getattr(scores, "face_detected", False),
            getattr(scores, "attention_score", 0.0),
        )

    async def get_session_summary(self) -> dict[str, object]:
        """Returns current session statistics for dashboard."""
        now = time.time() * 1000.0
        duration_ms = now - self._config.started_at
        accuracy = (
            (self._correct_count / self._question_count * 100.0)
            if self._question_count > 0
            else 0.0
        )
        return {
            "session_id": self._config.session_id,
            "student_id": self._config.student_id,
            "lesson_id": self._config.lesson_id,
            "duration_ms": duration_ms,
            "duration_minutes": duration_ms / 60000.0,
            "total_events": self._event_count,
            "questions_answered": self._question_count,
            "accuracy_percentage": round(accuracy, 1),
            "rewind_count": self._rewind_count,
        }

    async def close(self) -> None:
        """Flush queue, mark session as ended."""
        now = time.time() * 1000.0
        duration_ms = now - self._config.started_at
        accuracy = (
            (self._correct_count / self._question_count * 100.0)
            if self._question_count > 0
            else 0.0
        )
        self._session_repo.end_session(
            session_id=self._config.session_id,
            ended_at=now,
            total_duration_ms=duration_ms,
            completion_percentage=accuracy,
        )
        logger.info(
            "Collector closed. Session {} — {} events, {}min",
            self._config.session_id,
            self._event_count,
            round(duration_ms / 60000.0, 1),
        )
