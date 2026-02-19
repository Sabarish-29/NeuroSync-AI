"""
NeuroSync AI — Pydantic v2 event models for all signal types.

These models are the data contracts for the entire system. Every signal,
from behavioral to webcam to EEG, passes through these models.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


def _uuid() -> str:
    return str(uuid.uuid4())


def _now_ms() -> float:
    return time.time() * 1000.0


# =============================================================================
# Session configuration
# =============================================================================

class SessionConfig(BaseModel):
    """Configuration for a learning session."""
    session_id: str = Field(default_factory=_uuid)
    student_id: str
    lesson_id: str
    started_at: float = Field(default_factory=_now_ms)
    eeg_enabled: bool = False
    webcam_enabled: bool = False
    experiment_group: Optional[Literal["control", "treatment"]] = None


# =============================================================================
# Raw events
# =============================================================================

EventType = Literal[
    "video_play", "video_pause", "video_seek", "video_rewind",
    "question_shown", "question_answered", "answer_submitted",
    "lesson_started", "lesson_ended", "tab_hidden", "tab_visible",
    "scroll", "mouse_idle", "mouse_active", "click",
    "page_load", "session_start", "session_end",
]


class RawEvent(BaseModel):
    """Base event model — every interaction generates one of these."""
    event_id: str = Field(default_factory=_uuid)
    session_id: str
    student_id: str
    timestamp: float = Field(default_factory=_now_ms)
    event_type: EventType
    metadata: dict[str, Any] = Field(default_factory=dict)


class QuestionEvent(RawEvent):
    """Event for question-related interactions."""
    question_id: str
    concept_id: str
    answer_given: Optional[str] = None
    answer_correct: Optional[bool] = None
    response_time_ms: Optional[float] = None
    confidence_score: Optional[int] = None  # 1-5 self-reported
    attempt_number: int = 1


class VideoEvent(RawEvent):
    """Event for video playback interactions."""
    video_id: str
    playback_position_ms: float
    playback_speed: float = 1.0
    seek_from_ms: Optional[float] = None
    seek_to_ms: Optional[float] = None


class IdleEvent(RawEvent):
    """Event for idle/inactive periods."""
    idle_duration_ms: float
    preceding_event_type: str


# =============================================================================
# Signal result models (output from signal processors)
# =============================================================================

class SignalResult(BaseModel):
    """Base class for all signal processor outputs."""
    processor_name: str
    timestamp: float = Field(default_factory=_now_ms)
    values: dict[str, Any] = Field(default_factory=dict)


class ResponseTimeResult(SignalResult):
    """Output from the ResponseTimeSignal processor."""
    processor_name: str = "response_time"
    mean_response_time_ms: float = 0.0
    response_time_trend: Literal["stable", "increasing", "decreasing"] = "stable"
    fast_answer_rate: float = 0.0


class RewindResult(SignalResult):
    """Output from the RewindSignal processor."""
    processor_name: str = "rewind"
    rewinds_per_minute: float = 0.0
    rewind_burst_detected: bool = False
    repeated_segment_ids: list[str] = Field(default_factory=list)


class IdleResult(SignalResult):
    """Output from the IdleSignal processor."""
    processor_name: str = "idle"
    total_idle_time_ms: float = 0.0
    idle_frequency: float = 0.0
    longest_idle_ms: float = 0.0
    recent_idle_trend: Literal["stable", "increasing"] = "stable"


class InteractionVarianceResult(SignalResult):
    """Output from the InteractionVarianceSignal processor."""
    processor_name: str = "interaction_variance"
    interaction_variance: float = 0.0
    variance_trend: Literal["stable", "increasing", "erratic"] = "stable"
    fatigue_probability: float = 0.0


class ScrollResult(SignalResult):
    """Output from the ScrollBehaviorSignal processor."""
    processor_name: str = "scroll"
    mean_scroll_speed: float = 0.0
    scroll_pattern: Literal["engaged", "skimming", "rushing"] = "engaged"
    rapid_scroll_bursts: int = 0


class SessionPacingResult(SignalResult):
    """Output from the SessionPacingSignal processor."""
    processor_name: str = "session_pacing"
    session_duration_minutes: float = 0.0
    content_engagement_rate: float = 0.0
    performance_trajectory: Literal["improving", "stable", "declining"] = "stable"
    optimal_session_length_estimate: float = 30.0


# =============================================================================
# Moment detection results
# =============================================================================

class FrustrationResult(BaseModel):
    """Output from FrustrationDetector (M07)."""
    score: float = 0.0
    level: Literal["none", "watch", "warning", "critical"] = "none"
    dominant_signal: str = ""
    recommended_action: str = ""
    confidence: float = 0.0


class FatigueResult(BaseModel):
    """Output from FatigueDetector (M10)."""
    score: float = 0.0
    level: Literal["fresh", "mild", "tired", "critical"] = "fresh"
    session_minutes_elapsed: float = 0.0
    estimated_minutes_until_critical: Optional[float] = None
    break_recommended: bool = False
    break_mandatory: bool = False


class MasteryCheckResult(BaseModel):
    """Output from PseudoUnderstandingDetector (M14)."""
    question_id: str = ""
    concept_id: str = ""
    answer_correct: bool = False
    authenticity_score: float = 0.0
    flag: Literal["accept", "probe", "flag"] = "accept"
    reason: str = ""
    recommended_action: Literal[
        "accept_mastery",
        "ask_followup",
        "require_elaboration",
        "schedule_delayed_retest",
    ] = "accept_mastery"


class InsightResult(BaseModel):
    """Output from InsightDetector (M08)."""
    detected: bool = False
    confidence: float = 0.0
    window_open_until: Optional[float] = None
    preceding_struggle_duration_ms: float = 0.0
    recommended_chain_concept_count: int = 0


class RewardDecision(BaseModel):
    """Output from VariableRewardScheduler (M20)."""
    fire_reward: bool = False
    reward_type: Optional[str] = None
    reason: str = ""
    next_check_after_ms: int = 5000


# =============================================================================
# Fusion output models
# =============================================================================

class InterventionRequest(BaseModel):
    """A request to fire an intervention."""
    moment_id: str
    intervention_type: str
    urgency: Literal["immediate", "next_pause", "deferred"]
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    signals_triggered: list[str] = Field(default_factory=list)


class MomentFlags(BaseModel):
    """Complete output of one fusion cycle."""
    session_id: str
    timestamp: float = Field(default_factory=_now_ms)
    active_moments: list[str] = Field(default_factory=list)
    interventions_ready: list[InterventionRequest] = Field(default_factory=list)
    priority_intervention: Optional[InterventionRequest] = None
    all_signal_scores: dict[str, float] = Field(default_factory=dict)


# =============================================================================
# Knowledge Graph events (Step 3)
# =============================================================================

class ConceptEvent(BaseModel):
    """Event representing a student encountering or interacting with a concept."""
    event_id: str = Field(default_factory=_uuid)
    session_id: str
    student_id: str
    timestamp: float = Field(default_factory=_now_ms)
    concept_id: str
    concept_name: str = ""
    category: Literal["core", "prerequisite", "extension", "application", "misconception"] = "core"
    action: Literal["encountered", "answered", "reviewed", "struggled", "mastered"] = "encountered"
    score_delta: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class MasteryEvent(BaseModel):
    """Event representing a mastery level change for a concept."""
    event_id: str = Field(default_factory=_uuid)
    student_id: str
    concept_id: str
    timestamp: float = Field(default_factory=_now_ms)
    previous_score: float = 0.0
    new_score: float = 0.0
    previous_level: Literal["novice", "developing", "proficient", "mastered"] = "novice"
    new_level: Literal["novice", "developing", "proficient", "mastered"] = "novice"
    trigger: str = ""  # what caused the change (e.g., "correct_answer", "misconception_detected")
    session_id: Optional[str] = None


# =============================================================================
# NLP Pipeline events (Step 4)
# =============================================================================

class TextEvent(BaseModel):
    """Event representing text input from a student (answer, chat, note)."""
    event_id: str = Field(default_factory=_uuid)
    session_id: str
    student_id: str
    timestamp: float = Field(default_factory=_now_ms)
    text: str
    text_type: Literal["answer", "chat", "note", "search", "question"] = "answer"
    concept_id: Optional[str] = None
    question_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NLPResult(BaseModel):
    """Aggregated NLP analysis result for a piece of text."""
    text: str = ""
    sentiment_polarity: float = 0.0
    sentiment_subjectivity: float = 0.0
    sentiment_label: Literal["positive", "neutral", "negative", "frustrated"] = "neutral"
    complexity_score: float = 0.0
    complexity_label: Literal["simple", "moderate", "hard", "very_hard"] = "moderate"
    confusion_score: float = 0.0
    confusion_label: Literal["none", "mild", "moderate", "high"] = "none"
    answer_quality: Literal["low", "moderate", "good", "excellent"] = "moderate"
    answer_quality_score: float = 0.0
    keywords: list[str] = Field(default_factory=list)
    topic_drift_detected: bool = False
    word_count: int = 0
