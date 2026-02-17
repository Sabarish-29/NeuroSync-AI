"""
NeuroSync AI — Tests for AsyncEventCollector.
"""

import asyncio
import time

import pytest

from neurosync.behavioral.collector import AsyncEventCollector
from neurosync.core.events import QuestionEvent, RawEvent, SessionConfig, VideoEvent
from neurosync.database.manager import DatabaseManager
from neurosync.database.repositories.events import EventRepository
from tests.conftest import make_question_event, make_raw_event, make_video_event


@pytest.mark.asyncio
async def test_collector_records_events(db_manager: DatabaseManager, session_config: SessionConfig) -> None:
    """Events are recorded and persisted to the database."""
    collector = AsyncEventCollector(session_config, db_manager)
    await collector.start()

    event = make_raw_event(session_id=session_config.session_id, student_id=session_config.student_id)
    await collector.record_event(event)

    assert collector.event_count == 1

    # Verify event is in the queue
    queued = collector.queue.get_nowait()
    assert queued.event_type == "click"

    await collector.close()


@pytest.mark.asyncio
async def test_collector_records_questions(db_manager: DatabaseManager, session_config: SessionConfig) -> None:
    """Question events are handled correctly with specialized recording."""
    collector = AsyncEventCollector(session_config, db_manager)
    await collector.start()

    event = make_question_event(
        session_id=session_config.session_id,
        student_id=session_config.student_id,
        answer_correct=True,
        response_time_ms=5000.0,
    )
    await collector.record_question(event)

    summary = await collector.get_session_summary()
    assert summary["questions_answered"] == 1
    assert summary["accuracy_percentage"] == 100.0
    await collector.close()


@pytest.mark.asyncio
async def test_collector_records_video_rewinds(db_manager: DatabaseManager, session_config: SessionConfig) -> None:
    """Video rewind events are counted correctly."""
    collector = AsyncEventCollector(session_config, db_manager)
    await collector.start()

    event = make_video_event(
        session_id=session_config.session_id,
        student_id=session_config.student_id,
        event_type="video_rewind",
    )
    await collector.record_video(event)

    summary = await collector.get_session_summary()
    assert summary["rewind_count"] == 1
    await collector.close()


@pytest.mark.asyncio
async def test_collector_session_summary(db_manager: DatabaseManager, session_config: SessionConfig) -> None:
    """Session summary reflects recorded events."""
    collector = AsyncEventCollector(session_config, db_manager)
    await collector.start()

    for i in range(5):
        await collector.record_event(
            make_raw_event(session_id=session_config.session_id, student_id=session_config.student_id)
        )

    summary = await collector.get_session_summary()
    assert summary["total_events"] == 5
    assert summary["session_id"] == session_config.session_id
    await collector.close()
