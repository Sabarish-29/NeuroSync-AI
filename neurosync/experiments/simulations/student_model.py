"""
Student Model — simulates realistic student behaviour.

Generates synthetic behavioural and webcam signals that mimic how
real students interact during a lesson.  Used for experiment
dry-runs and demo modes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from neurosync.fusion.state import BehavioralSignals, WebcamSignals


@dataclass
class StudentProfile:
    """Describes a virtual student's characteristics."""

    student_id: str = "sim_student"
    attention_baseline: float = 0.8
    frustration_tendency: float = 0.2
    fatigue_rate: float = 0.1        # per-minute fatigue accumulation
    quiz_ability: float = 0.7        # probability of correct answer
    seed: int = 42


class StudentModel:
    """Simulates a student progressing through a lesson."""

    def __init__(self, profile: Optional[StudentProfile] = None):
        self.profile = profile or StudentProfile()
        self.rng = random.Random(self.profile.seed)
        self._minute = 0
        self._fatigue = 0.0
        self._frustration = 0.0

    def advance_minute(self) -> None:
        """Advance the simulation clock by one minute."""
        self._minute += 1
        self._fatigue = min(
            1.0, self._fatigue + self.profile.fatigue_rate * self.rng.uniform(0.5, 1.5)
        )
        # Frustration builds if fatigue is high
        if self._fatigue > 0.5:
            self._frustration = min(
                1.0,
                self._frustration + self.profile.frustration_tendency * 0.1,
            )

    def get_behavioral_signals(self) -> BehavioralSignals:
        """Generate behavioural signals for the current minute."""
        return BehavioralSignals(
            frustration_score=round(self._frustration, 3),
            fatigue_score=round(self._fatigue, 3),
            response_time_mean_ms=300 + self._fatigue * 400 + self.rng.uniform(-50, 50),
            response_time_trend="increasing" if self._fatigue > 0.5 else "stable",
            fast_answer_rate=max(0, 0.3 - self._fatigue * 0.2),
            rewinds_per_minute=self.rng.uniform(0, 2) if self._frustration > 0.3 else 0.0,
            rewind_burst=self._frustration > 0.6,
            idle_frequency=self._fatigue * 3,
            interaction_variance=self.rng.uniform(0.1, 0.5),
        )

    def get_webcam_signals(self) -> WebcamSignals:
        """Generate webcam signals for the current minute."""
        attention = max(
            0,
            self.profile.attention_baseline
            - self._fatigue * 0.3
            - self._frustration * 0.2
            + self.rng.uniform(-0.1, 0.1),
        )
        return WebcamSignals(
            attention_score=round(min(1.0, attention), 3),
            off_screen_triggered=attention < 0.3,
            off_screen_duration_ms=self.rng.randint(0, 5000) if attention < 0.3 else 0,
            frustration_boost=round(self._frustration * 0.3, 3),
            boredom_score=round(max(0, self._fatigue - 0.3) * 0.5, 3),
            discomfort_probability=0.0,
            fatigue_boost=round(self._fatigue * 0.2, 3),
            face_detected=True,
        )

    def answer_quiz(self) -> bool:
        """Simulate answering a quiz question."""
        p = self.profile.quiz_ability - self._fatigue * 0.15
        return self.rng.random() < p

    @property
    def current_minute(self) -> int:
        return self._minute

    @property
    def fatigue(self) -> float:
        return self._fatigue

    @property
    def frustration(self) -> float:
        return self._frustration

    def reset(self) -> None:
        self._minute = 0
        self._fatigue = 0.0
        self._frustration = 0.0
        self.rng = random.Random(self.profile.seed)
