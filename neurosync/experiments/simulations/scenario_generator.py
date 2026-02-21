"""
Scenario Generator — creates test scenarios for experiments.

Generates pre-configured learning scenarios that exercise
specific moments and intervention paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from neurosync.core.constants import (
    MOMENT_ATTENTION_DROP,
    MOMENT_COGNITIVE_OVERLOAD,
    MOMENT_FRUSTRATION,
    MOMENT_FATIGUE,
    MOMENT_KNOWLEDGE_GAP,
    MOMENT_MISCONCEPTION,
    MOMENT_FORGETTING_CURVE,
    MOMENT_PLATEAU_ESCAPE,
)
from neurosync.fusion.state import BehavioralSignals, WebcamSignals


@dataclass
class ScenarioStep:
    """One step in a scenario."""

    minute: int
    description: str
    behavioral: BehavioralSignals | None = None
    webcam: WebcamSignals | None = None
    expected_moments: list[str] = field(default_factory=list)


@dataclass
class Scenario:
    """A complete test scenario."""

    name: str
    description: str
    duration_minutes: int
    steps: list[ScenarioStep] = field(default_factory=list)
    target_moments: list[str] = field(default_factory=list)


class ScenarioGenerator:
    """Generate pre-built scenarios for testing and demos."""

    @staticmethod
    def attention_drop_scenario() -> Scenario:
        """Student looks away → M01 fires → returns focus."""
        return Scenario(
            name="Attention Drop",
            description="Student loses attention at minute 5",
            duration_minutes=10,
            target_moments=[MOMENT_ATTENTION_DROP],
            steps=[
                ScenarioStep(
                    minute=0,
                    description="Normal attentive learning",
                    webcam=WebcamSignals(attention_score=0.9, face_detected=True),
                ),
                ScenarioStep(
                    minute=5,
                    description="Student looks away",
                    webcam=WebcamSignals(
                        attention_score=0.15,
                        off_screen_triggered=True,
                        off_screen_duration_ms=5000,
                        face_detected=True,
                    ),
                    expected_moments=[MOMENT_ATTENTION_DROP],
                ),
                ScenarioStep(
                    minute=6,
                    description="Student returns focus",
                    webcam=WebcamSignals(attention_score=0.85, face_detected=True),
                ),
            ],
        )

    @staticmethod
    def cognitive_overload_scenario() -> Scenario:
        """Dense content overwhelms student → M02 fires."""
        return Scenario(
            name="Cognitive Overload",
            description="Complex content causes cognitive overload",
            duration_minutes=10,
            target_moments=[MOMENT_COGNITIVE_OVERLOAD],
            steps=[
                ScenarioStep(
                    minute=0,
                    description="Normal content",
                    behavioral=BehavioralSignals(rewinds_per_minute=0.0),
                ),
                ScenarioStep(
                    minute=4,
                    description="Dense content, student struggling",
                    behavioral=BehavioralSignals(
                        rewinds_per_minute=3.0,
                        rewind_burst=True,
                        response_time_mean_ms=800,
                        response_time_trend="increasing",
                    ),
                    expected_moments=[MOMENT_COGNITIVE_OVERLOAD],
                ),
            ],
        )

    @staticmethod
    def frustration_buildup_scenario() -> Scenario:
        """Student gets frustrated → M07 fires."""
        return Scenario(
            name="Frustration Buildup",
            description="Difficult section causes rising frustration",
            duration_minutes=15,
            target_moments=[MOMENT_FRUSTRATION],
            steps=[
                ScenarioStep(
                    minute=0,
                    description="Easy intro",
                    behavioral=BehavioralSignals(frustration_score=0.1),
                ),
                ScenarioStep(
                    minute=8,
                    description="Difficult section, frustration rising",
                    behavioral=BehavioralSignals(
                        frustration_score=0.75,
                        rewind_burst=True,
                        idle_frequency=4.0,
                    ),
                    webcam=WebcamSignals(
                        frustration_boost=0.4,
                        attention_score=0.4,
                        face_detected=True,
                    ),
                    expected_moments=[MOMENT_FRUSTRATION],
                ),
            ],
        )

    @staticmethod
    def full_session_scenario() -> Scenario:
        """Complete session hitting multiple moments."""
        return Scenario(
            name="Full Session",
            description="A complete 15-minute session exercising multiple moments",
            duration_minutes=15,
            target_moments=[
                MOMENT_ATTENTION_DROP,
                MOMENT_COGNITIVE_OVERLOAD,
                MOMENT_FRUSTRATION,
                MOMENT_FATIGUE,
            ],
            steps=[
                ScenarioStep(minute=0, description="Start — attentive"),
                ScenarioStep(
                    minute=3,
                    description="Attention drop",
                    webcam=WebcamSignals(
                        attention_score=0.15,
                        off_screen_triggered=True,
                        off_screen_duration_ms=4000,
                        face_detected=True,
                    ),
                    expected_moments=[MOMENT_ATTENTION_DROP],
                ),
                ScenarioStep(
                    minute=7,
                    description="Cognitive overload",
                    behavioral=BehavioralSignals(
                        rewinds_per_minute=3.5,
                        rewind_burst=True,
                    ),
                    expected_moments=[MOMENT_COGNITIVE_OVERLOAD],
                ),
                ScenarioStep(
                    minute=10,
                    description="Frustration",
                    behavioral=BehavioralSignals(frustration_score=0.8),
                    expected_moments=[MOMENT_FRUSTRATION],
                ),
                ScenarioStep(
                    minute=14,
                    description="Fatigue",
                    behavioral=BehavioralSignals(
                        fatigue_score=0.75,
                        idle_frequency=5.0,
                        interaction_variance=0.1,
                    ),
                    expected_moments=[MOMENT_FATIGUE],
                ),
            ],
        )

    @classmethod
    def all_scenarios(cls) -> list[Scenario]:
        """Return all pre-built scenarios."""
        return [
            cls.attention_drop_scenario(),
            cls.cognitive_overload_scenario(),
            cls.frustration_buildup_scenario(),
            cls.full_session_scenario(),
        ]
