"""
NeuroSync AI — Shared test fixtures.
"""

import os
import tempfile
import time
import uuid
from pathlib import Path

import pytest

from neurosync.core.events import (
    IdleEvent,
    QuestionEvent,
    RawEvent,
    SessionConfig,
    VideoEvent,
)
from neurosync.database.manager import DatabaseManager


@pytest.fixture
def db_manager(tmp_path: Path) -> DatabaseManager:
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path)
    db.initialise()
    yield db  # type: ignore[misc]
    db.close()


@pytest.fixture
def session_config() -> SessionConfig:
    """Create a test session config."""
    return SessionConfig(
        student_id="test_student",
        lesson_id="test_lesson",
        started_at=time.time() * 1000,
    )


@pytest.fixture
def base_timestamp() -> float:
    """Base timestamp (ms) for creating events."""
    return time.time() * 1000


def make_raw_event(
    session_id: str = "test_session",
    student_id: str = "test_student",
    event_type: str = "click",
    timestamp: float | None = None,
    metadata: dict | None = None,
) -> RawEvent:
    """Helper to create a raw event."""
    return RawEvent(
        session_id=session_id,
        student_id=student_id,
        event_type=event_type,  # type: ignore[arg-type]
        timestamp=timestamp or time.time() * 1000,
        metadata=metadata or {},
    )


def make_question_event(
    session_id: str = "test_session",
    student_id: str = "test_student",
    question_id: str | None = None,
    concept_id: str = "concept_1",
    answer_correct: bool = True,
    response_time_ms: float = 5000.0,
    confidence_score: int = 3,
    timestamp: float | None = None,
) -> QuestionEvent:
    """Helper to create a question event."""
    return QuestionEvent(
        session_id=session_id,
        student_id=student_id,
        event_type="answer_submitted",
        timestamp=timestamp or time.time() * 1000,
        question_id=question_id or str(uuid.uuid4())[:8],
        concept_id=concept_id,
        answer_correct=answer_correct,
        response_time_ms=response_time_ms,
        confidence_score=confidence_score,
    )


def make_video_event(
    session_id: str = "test_session",
    student_id: str = "test_student",
    event_type: str = "video_rewind",
    timestamp: float | None = None,
    playback_position_ms: float = 60000.0,
) -> VideoEvent:
    """Helper to create a video event."""
    return VideoEvent(
        session_id=session_id,
        student_id=student_id,
        event_type=event_type,  # type: ignore[arg-type]
        timestamp=timestamp or time.time() * 1000,
        video_id="test_video",
        playback_position_ms=playback_position_ms,
    )


def make_idle_event(
    session_id: str = "test_session",
    student_id: str = "test_student",
    idle_duration_ms: float = 5000.0,
    timestamp: float | None = None,
) -> IdleEvent:
    """Helper to create an idle event."""
    return IdleEvent(
        session_id=session_id,
        student_id=student_id,
        event_type="mouse_idle",
        timestamp=timestamp or time.time() * 1000,
        idle_duration_ms=idle_duration_ms,
        preceding_event_type="click",
    )


# =====================================================================
# Step 2 — Webcam fixtures (re-export from conftest_webcam)
# =====================================================================
from tests.conftest_webcam import (  # noqa: E402, F401
    mock_frame_face_centered,
    mock_frame_no_face,
    mock_landmarks_neutral,
    mock_landmarks_looking_left,
    mock_landmarks_no_face,
    mock_landmarks_frustrated,
    mock_landmarks_bored,
    mock_landmarks_closed_eyes,
)


# =====================================================================
# Step 3 — Knowledge graph fixtures (re-export from conftest_graph)
# =====================================================================
from tests.conftest_graph import (  # noqa: E402, F401
    mock_graph_manager,
    seeded_graph,
)


# =====================================================================
# Step 4 — NLP fixtures (re-export from conftest_nlp)
# =====================================================================
from tests.conftest_nlp import (  # noqa: E402, F401
    nlp_pipeline,
    text_event,
)


# =====================================================================
# Step 6 — Intervention fixtures (re-export from conftest_interventions)
# =====================================================================
from tests.conftest_interventions import (  # noqa: E402, F401
    mock_openai_response,
    cache_manager,
    cost_tracker,
    generator,
)
