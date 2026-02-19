"""
NeuroSync AI — Fusion test fixtures (Step 5).

Pre-built FusionState snapshots for every trigger scenario so
agent tests are concise and deterministic.
"""

from __future__ import annotations

import time

import pytest

from neurosync.fusion.state import (
    BehavioralSignals,
    FusionState,
    KnowledgeSignals,
    NLPSignals,
    WebcamSignals,
)

# ── base helpers ────────────────────────────────────────────────────

_TS = time.time()


def _base_state(**overrides) -> FusionState:
    """Build a FusionState with sensible defaults, applying overrides."""
    defaults = dict(
        session_id="test-session",
        student_id="test-student",
        timestamp=_TS,
        cycle_number=1,
        behavioral=BehavioralSignals(),
        webcam=WebcamSignals(),
        knowledge=KnowledgeSignals(),
        nlp=None,
        session_duration_minutes=5.0,
        lesson_position_ms=30_000.0,
        recent_interventions=[],
        agent_states={},
    )
    defaults.update(overrides)
    return FusionState(**defaults)


# ── fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def normal_state() -> FusionState:
    """Normal learning — no interventions needed."""
    return _base_state()


@pytest.fixture
def attention_drop_state() -> FusionState:
    """Webcam reports gaze off-screen."""
    return _base_state(
        webcam=WebcamSignals(
            off_screen_triggered=True,
            off_screen_duration_ms=4200.0,
            face_detected=True,
        ),
    )


@pytest.fixture
def overload_state() -> FusionState:
    """NLP detects high complexity."""
    return _base_state(
        nlp=NLPSignals(
            overload_detected=True,
            target_simplification_phrase="thylakoid membranes absorb photons",
            max_complexity_score=0.82,
        ),
        behavioral=BehavioralSignals(response_time_trend="increasing"),
    )


@pytest.fixture
def frustration_critical_state() -> FusionState:
    """Frustration above critical threshold."""
    return _base_state(
        behavioral=BehavioralSignals(frustration_score=0.78),
    )


@pytest.fixture
def boredom_state() -> FusionState:
    """High mastery + webcam boredom."""
    return _base_state(
        knowledge=KnowledgeSignals(current_segment_mastery=0.92),
        webcam=WebcamSignals(boredom_score=0.70, face_detected=True),
    )


@pytest.fixture
def confidence_collapse_state() -> FusionState:
    """Moderate frustration → confidence collapse signal."""
    return _base_state(
        behavioral=BehavioralSignals(frustration_score=0.55),
    )


@pytest.fixture
def fatigue_critical_state() -> FusionState:
    """Fatigue above mandatory break threshold."""
    return _base_state(
        behavioral=BehavioralSignals(fatigue_score=0.82),
        session_duration_minutes=35.0,
    )


@pytest.fixture
def memory_overflow_state() -> FusionState:
    """NLP chunk tracker reports overflow risk."""
    return _base_state(
        nlp=NLPSignals(
            overflow_risk=True,
            unconfirmed_count=5,
            concepts_to_review=["c1", "c2", "c3", "c4", "c5"],
        ),
    )


@pytest.fixture
def misconception_state() -> FusionState:
    """Knowledge graph has pending misconceptions."""
    return _base_state(
        knowledge=KnowledgeSignals(
            misconceptions_pending=["concept_photosynthesis"],
        ),
    )


@pytest.fixture
def gap_state() -> FusionState:
    """Knowledge graph has pending gaps."""
    return _base_state(
        knowledge=KnowledgeSignals(
            gaps_pending=["concept_chlorophyll", "concept_atp"],
        ),
    )


@pytest.fixture
def plateau_state() -> FusionState:
    """Knowledge graph detected learning plateau."""
    return _base_state(
        knowledge=KnowledgeSignals(
            plateau_detected=True,
            plateau_concept_id="concept_calvin_cycle",
        ),
    )
