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
    NLPResult,
    QuestionEvent,
    RawEvent,
    SessionConfig,
    TextEvent,
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
    # Step 4 — NLP text event recording
    # ------------------------------------------------------------------

    async def record_text_event(
        self,
        event: TextEvent,
        expected_keywords: list[str] | None = None,
        reference_keywords: list[str] | None = None,
    ) -> NLPResult:
        """
        Record a text event and run NLP analysis.

        Parameters
        ----------
        event : TextEvent
            The student text event (answer, chat, note, etc.).
        expected_keywords : list[str], optional
            Expected concept keywords for answer quality scoring.
        reference_keywords : list[str], optional
            Topic reference keywords for drift detection.

        Returns
        -------
        NLPResult
            The NLP analysis result for the text.
        """
        event.session_id = self._config.session_id
        event.student_id = self._config.student_id
        self._event_count += 1

        # Lazy-init the NLP pipeline
        if not hasattr(self, "_nlp_pipeline"):
            from neurosync.nlp.pipeline import NLPPipeline
            self._nlp_pipeline = NLPPipeline()

        result = self._nlp_pipeline.analyze(
            text=event.text,
            expected_keywords=expected_keywords,
            reference_keywords=reference_keywords,
        )

        logger.debug(
            "Text event recorded: type={}, sentiment={}, confusion={}",
            event.text_type,
            result.sentiment_label,
            result.confusion_label,
        )
        return result

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

    # ------------------------------------------------------------------
    # Step 3 — Knowledge graph concept encounter
    # ------------------------------------------------------------------

    async def record_concept_encounter(
        self,
        concept_id: str,
        concept_name: str = "",
        category: str = "core",
        action: str = "encountered",
        score_delta: float = 0.0,
        metadata: dict | None = None,
    ) -> None:
        """
        Record that the student encountered or interacted with a concept.

        Creates a ConceptEvent and pushes it to the queue for downstream
        knowledge-graph processors to consume.

        Parameters
        ----------
        concept_id : str
            Unique concept identifier.
        concept_name : str
            Human-readable concept name.
        category : str
            One of: core, prerequisite, extension, application, misconception.
        action : str
            One of: encountered, answered, reviewed, struggled, mastered.
        score_delta : float
            Change in mastery score (positive or negative).
        metadata : dict, optional
            Extra data about the encounter.
        """
        from neurosync.core.events import ConceptEvent  # lazy import

        event = ConceptEvent(
            session_id=self._config.session_id,
            student_id=self._config.student_id,
            concept_id=concept_id,
            concept_name=concept_name,
            category=category,  # type: ignore[arg-type]
            action=action,  # type: ignore[arg-type]
            score_delta=score_delta,
            metadata=metadata or {},
        )
        self._event_count += 1
        logger.debug(
            "Concept encounter recorded: {} ({}) — action={}, delta={:.2f}",
            concept_id, concept_name, action, score_delta,
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
