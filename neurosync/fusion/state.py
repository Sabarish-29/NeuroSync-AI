"""
NeuroSync AI — Fusion state models.

Pydantic v2 models used as the data flowing through the LangGraph
state machine.  Each 250 ms fusion cycle creates a *FusionState*
snapshot, feeds it through all agents, and collects
*InterventionProposal* outputs.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ── helpers ──────────────────────────────────────────────────────────

def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> float:
    return time.time()


# ── signal aggregation models ───────────────────────────────────────


class BehavioralSignals(BaseModel):
    """Aggregated behavioural signals (from Step 1)."""
    frustration_score: float = 0.0
    fatigue_score: float = 0.0
    response_time_mean_ms: float = 0.0
    response_time_trend: Literal["stable", "increasing", "decreasing"] = "stable"
    fast_answer_rate: float = 0.0
    rewinds_per_minute: float = 0.0
    rewind_burst: bool = False
    idle_frequency: float = 0.0
    interaction_variance: float = 0.0
    insight_detected: bool = False
    reward_ready: bool = False


class WebcamSignals(BaseModel):
    """Aggregated webcam signals (from Step 2).  ``None`` when webcam off."""
    attention_score: float = 0.8
    off_screen_triggered: bool = False
    off_screen_duration_ms: float = 0.0
    frustration_boost: float = 0.0
    boredom_score: float = 0.0
    discomfort_probability: float = 0.0
    fatigue_boost: float = 0.0
    face_detected: bool = True


class KnowledgeSignals(BaseModel):
    """Aggregated knowledge-graph signals (from Step 3)."""
    current_segment_mastery: float = 0.0
    gaps_pending: list[str] = Field(default_factory=list)
    misconceptions_pending: list[str] = Field(default_factory=list)
    plateau_detected: bool = False
    plateau_concept_id: Optional[str] = None


class NLPSignals(BaseModel):
    """Aggregated NLP signals (from Step 4)."""
    overload_detected: bool = False
    target_simplification_phrase: Optional[str] = None
    max_complexity_score: float = 0.0
    confusion_score: float = 0.0
    entities_found: list[str] = Field(default_factory=list)
    overflow_risk: bool = False
    unconfirmed_count: int = 0
    concepts_to_review: list[str] = Field(default_factory=list)


# ── per-agent bookkeeping ───────────────────────────────────────────


class AgentState(BaseModel):
    """Tracking state for a single agent across cycles."""
    agent_name: str
    last_detection_timestamp: float = 0.0
    detection_count_session: int = 0
    cooldown_until: float = 0.0
    active_moments: list[str] = Field(default_factory=list)
    confidence: float = 0.0


# ── intervention proposal ───────────────────────────────────────────


class InterventionProposal(BaseModel):
    """
    An intervention proposed by an agent.
    The prioritiser / cooldown tracker will decide which ones actually fire.
    """
    intervention_id: str = Field(default_factory=_uuid)
    moment_id: str
    agent_name: str
    intervention_type: str
    urgency: Literal["critical", "high", "medium", "low"] = "medium"
    confidence: float = 0.0
    payload: dict[str, Any] = Field(default_factory=dict)
    signals_supporting: list[str] = Field(default_factory=list)
    cooldown_seconds: int = 120
    timestamp: float = Field(default_factory=_now)


# ── agent evaluation result ─────────────────────────────────────────


class AgentEvaluation(BaseModel):
    """Return type from ``agent.evaluate()``."""
    agent_name: str
    detected_moments: list[str] = Field(default_factory=list)
    interventions: list[InterventionProposal] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""


# ── complete fusion state ────────────────────────────────────────────


class FusionState(BaseModel):
    """
    Complete snapshot at one point in time.  Flows through the
    LangGraph as the shared state object.
    """
    # Identifiers
    session_id: str
    student_id: str
    timestamp: float = Field(default_factory=_now)
    cycle_number: int = 0

    # Signals from the four layers
    behavioral: BehavioralSignals = Field(default_factory=BehavioralSignals)
    webcam: Optional[WebcamSignals] = None
    knowledge: KnowledgeSignals = Field(default_factory=KnowledgeSignals)
    nlp: Optional[NLPSignals] = None

    # Session context
    session_duration_minutes: float = 0.0
    lesson_position_ms: float = 0.0
    recent_interventions: list[str] = Field(default_factory=list)

    # Agent bookkeeping (updated each cycle)
    agent_states: dict[str, AgentState] = Field(default_factory=dict)

    # Collected proposals (populated by agent nodes)
    proposed_interventions: list[InterventionProposal] = Field(default_factory=list)
