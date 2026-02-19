"""
Shared fixtures for Step 9 — Pre-Lesson Readiness Protocol tests.
"""

from __future__ import annotations

import pytest

from neurosync.readiness.assessments.self_report import SelfReportResult
from neurosync.readiness.assessments.physiological import PhysiologicalResult
from neurosync.readiness.assessments.behavioral import BehavioralResult, WarmupAnswer


@pytest.fixture
def low_anxiety_responses() -> dict[str, int]:
    """Self-report responses indicating low anxiety."""
    return {"familiarity": 5, "difficulty_perception": 1, "emotional_state": 1}


@pytest.fixture
def high_anxiety_responses() -> dict[str, int]:
    """Self-report responses indicating high anxiety."""
    return {"familiarity": 1, "difficulty_perception": 5, "emotional_state": 5}


@pytest.fixture
def normal_warmup_answers() -> list[WarmupAnswer]:
    """Warmup answers with normal response times and high accuracy."""
    return [
        WarmupAnswer(question_id="q1", correct=True, response_time_seconds=6.0),
        WarmupAnswer(question_id="q2", correct=True, response_time_seconds=7.0),
        WarmupAnswer(question_id="q3", correct=True, response_time_seconds=5.0),
    ]


@pytest.fixture
def slow_warmup_answers() -> list[WarmupAnswer]:
    """Warmup answers with slow, variable response times."""
    return [
        WarmupAnswer(question_id="q1", correct=False, response_time_seconds=16.0),
        WarmupAnswer(question_id="q2", correct=True, response_time_seconds=20.0),
        WarmupAnswer(question_id="q3", correct=False, response_time_seconds=12.0),
    ]
