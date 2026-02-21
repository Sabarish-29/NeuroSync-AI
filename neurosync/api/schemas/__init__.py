"""Pydantic request schemas for the NeuroSync API."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class SessionStartRequest(BaseModel):
    """Request to start a new learning session."""

    session_id: str
    student_id: str
    lesson_id: str = ""
    webcam_enabled: bool = False


class SessionEndRequest(BaseModel):
    """Request to end a learning session."""

    session_id: str


class EventRequest(BaseModel):
    """Generic learning event from the frontend."""

    session_id: str
    event_type: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Video-specific
    playback_position_ms: float = 0.0
    seek_from_ms: float = 0.0
    seek_to_ms: float = 0.0
    # Question-specific
    question_id: str = ""
    concept_id: str = ""
    answer_given: str = ""
    answer_correct: bool = False
    response_time_ms: float = 0.0
    confidence_score: float = 0.0


class BehavioralSignalsRequest(BaseModel):
    """Manual behavioral signal input."""

    session_id: str
    frustration_score: float = 0.0
    fatigue_score: float = 0.0
    response_time_mean_ms: float = 500.0
    response_time_trend: float = 0.0
    fast_answer_rate: float = 0.0
    rewinds_per_minute: float = 0.0
    rewind_burst: bool = False
    idle_frequency: float = 0.0
    interaction_variance: float = 0.5
    insight_detected: bool = False
    reward_ready: bool = False


class WebcamSignalsRequest(BaseModel):
    """Manual webcam signal input."""

    session_id: str
    attention_score: float = 1.0
    off_screen_triggered: bool = False
    off_screen_duration_ms: float = 0.0
    frustration_boost: float = 0.0
    boredom_score: float = 0.0
    discomfort_probability: float = 0.0
    fatigue_boost: float = 0.0
    face_detected: bool = True


class ReadinessRequest(BaseModel):
    """Request to run a readiness check."""

    session_id: str = "readiness-session"
    student_id: str
    lesson_topic: str
    self_report_responses: Optional[dict[str, int]] = None
    blink_rate: Optional[float] = None


class ReviewSubmitRequest(BaseModel):
    """Submit a spaced-repetition review result."""

    student_id: str
    concept_id: str
    score: float


class FusionCycleRequest(BaseModel):
    """Request to run a single fusion cycle."""

    session_id: str
    behavioral: Optional[BehavioralSignalsRequest] = None
    webcam: Optional[WebcamSignalsRequest] = None


class ContentUploadRequest(BaseModel):
    """Metadata for content upload (file sent separately)."""

    title: str = ""
    generate_video: bool = False
    generate_slides: bool = True
    generate_notes: bool = True
    generate_story: bool = True
    generate_quiz: bool = True


class KnowledgeMapRequest(BaseModel):
    """Request for knowledge map data."""

    student_id: str
    course_id: str = ""
