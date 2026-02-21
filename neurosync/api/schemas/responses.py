"""Pydantic response schemas for the NeuroSync API."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    """Generic status response."""

    status: str = "ok"
    message: str = ""


class SessionResponse(BaseModel):
    """Response after starting / ending a session."""

    session_id: str
    status: str


class EventResponse(BaseModel):
    """Response after recording an event."""

    status: str = "recorded"
    event_type: str = ""


class SignalSnapshot(BaseModel):
    """Real-time signal snapshot sent over WebSocket."""

    session_id: str = ""
    attention: float = 1.0
    frustration: float = 0.0
    fatigue: float = 0.0
    boredom: float = 0.0
    engagement: float = 1.0
    cognitive_load: float = 0.3
    emotion: str = "neutral"
    face_detected: bool = True
    timestamp: float = 0.0


class InterventionResponse(BaseModel):
    """An intervention triggered during a session."""

    intervention_id: str = ""
    moment_id: str = ""
    agent_name: str = ""
    intervention_type: str = ""
    urgency: str = "medium"
    confidence: float = 0.0
    payload: dict[str, Any] = Field(default_factory=dict)
    content: str = ""
    cooldown_seconds: float = 30.0


class FusionCycleResponse(BaseModel):
    """Result of a single fusion cycle."""

    session_id: str
    interventions: list[InterventionResponse] = Field(default_factory=list)
    signals: SignalSnapshot = Field(default_factory=SignalSnapshot)


class ContentGenerationResponse(BaseModel):
    """Response from content generation pipeline."""

    task_id: str = ""
    status: str = "processing"
    progress: float = 0.0
    title: str = ""
    concept_count: int = 0
    slide_count: int = 0
    question_count: int = 0
    video_duration: str = ""
    formats_generated: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class DueReviewResponse(BaseModel):
    """A single due review item."""

    concept_id: str
    scheduled_at: float = 0.0
    review_number: int = 1
    predicted_retention: float = 1.0
    quiz: dict[str, Any] = Field(default_factory=dict)


class DueReviewsListResponse(BaseModel):
    """List of due reviews for a student."""

    student_id: str
    reviews: list[DueReviewResponse] = Field(default_factory=list)
    total: int = 0


class ReviewResultResponse(BaseModel):
    """Result after submitting a review."""

    student_id: str
    concept_id: str
    score: float
    next_review_at: float = 0.0
    status: str = "recorded"


class ReadinessResponse(BaseModel):
    """Readiness check result."""

    check_id: str = ""
    session_id: str = ""
    student_id: str = ""
    lesson_topic: str = ""
    readiness_score: float = 0.0
    anxiety_score: float = 0.0
    status: str = "ready"
    recommendation: str = ""
    breathing_offered: bool = False


class KnowledgeNodeResponse(BaseModel):
    """A node in the knowledge graph."""

    id: str
    label: str
    category: str = ""
    mastery: float = 0.0
    status: str = "not_started"


class KnowledgeEdgeResponse(BaseModel):
    """An edge in the knowledge graph."""

    source: str
    target: str
    relationship: str = "prerequisite"


class KnowledgeMapResponse(BaseModel):
    """Knowledge map for a student."""

    student_id: str
    nodes: list[KnowledgeNodeResponse] = Field(default_factory=list)
    edges: list[KnowledgeEdgeResponse] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "5.1.0"
    active_sessions: int = 0
