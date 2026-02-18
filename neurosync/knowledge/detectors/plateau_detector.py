"""
NeuroSync AI — Plateau Detector (M22).

Detects when a student's mastery score has stagnated despite continued
effort. Suggests strategy changes to break through the plateau.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import KNOWLEDGE_THRESHOLDS
from neurosync.core.constants import MOMENT_PLATEAU_ESCAPE


@dataclass
class PlateauResult:
    """Result from the plateau detector."""
    plateau_detected: bool = False
    concept_id: str = ""
    current_score: float = 0.0
    attempts: int = 0
    score_variance: float = 0.0
    duration_minutes: float = 0.0
    recommended_action: str = ""
    confidence: float = 0.0


class PlateauDetector:
    """
    Detects mastery plateaus (M22).

    A plateau is when a student has made many attempts at a concept but
    their mastery score barely changes — they're stuck. The system needs
    to suggest a different approach (worked examples, peer discussion,
    alternative explanation, etc.).
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager
        self._min_attempts = int(KNOWLEDGE_THRESHOLDS["PLATEAU_MIN_ATTEMPTS"])
        self._variance_max = float(KNOWLEDGE_THRESHOLDS["PLATEAU_VARIANCE_MAX"])
        self._min_duration = float(KNOWLEDGE_THRESHOLDS["PLATEAU_DURATION_MINUTES"])
        self._switch_score = float(KNOWLEDGE_THRESHOLDS["PLATEAU_STRATEGY_SWITCH_SCORE"])
        # Track score history per (student_id, concept_id)
        self._score_history: dict[tuple[str, str], list[tuple[float, float]]] = {}

    def record_score(
        self,
        student_id: str,
        concept_id: str,
        score: float,
        timestamp: Optional[float] = None,
    ) -> None:
        """Record a mastery score data point for plateau analysis."""
        key = (student_id, concept_id)
        if key not in self._score_history:
            self._score_history[key] = []
        ts = timestamp or time.time()
        self._score_history[key].append((ts, score))

    def detect(
        self,
        student_id: str,
        concept_id: str,
        current_score: float,
        attempts: int,
        first_seen: Optional[float] = None,
    ) -> PlateauResult:
        """
        Detect a mastery plateau.

        Parameters
        ----------
        student_id : str
            The student.
        concept_id : str
            The concept to check.
        current_score : float
            Current mastery score.
        attempts : int
            Total attempts at this concept.
        first_seen : float, optional
            Timestamp of first encounter (for duration calculation).
        """
        if attempts < self._min_attempts:
            return PlateauResult(
                concept_id=concept_id,
                current_score=current_score,
                attempts=attempts,
            )

        # Calculate duration
        now = time.time()
        duration_min = 0.0
        if first_seen is not None and first_seen > 0:
            duration_min = (now - first_seen) / 60.0

        # Calculate variance from score history
        key = (student_id, concept_id)
        history = self._score_history.get(key, [])

        if len(history) >= 3:
            scores = [s for _, s in history[-self._min_attempts:]]
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        elif attempts >= self._min_attempts:
            # No detailed history, estimate from score and attempts
            variance = 0.01  # assume low variance since we're checking
        else:
            return PlateauResult(
                concept_id=concept_id,
                current_score=current_score,
                attempts=attempts,
            )

        # Plateau = low variance + enough attempts + enough duration
        is_plateau = (
            variance <= self._variance_max
            and attempts >= self._min_attempts
            and (duration_min >= self._min_duration or first_seen is None)
        )

        if not is_plateau:
            return PlateauResult(
                concept_id=concept_id,
                current_score=current_score,
                attempts=attempts,
                score_variance=variance,
                duration_minutes=duration_min,
            )

        # Determine recommended action based on current score
        if current_score < 0.3:
            action = "try_worked_examples"
        elif current_score <= 0.5:
            action = "try_alternative_explanation"
        elif current_score < 0.7:
            action = "try_peer_discussion"
        else:
            action = "try_application_problem"

        # Confidence
        confidence = min(1.0, 0.6 + (1.0 - variance) * 0.2 + min(attempts / 20.0, 0.2))

        logger.info(
            "M22 Plateau detected: {} on {} (score={:.2f}, attempts={}, var={:.4f})",
            student_id, concept_id, current_score, attempts, variance,
        )

        return PlateauResult(
            plateau_detected=True,
            concept_id=concept_id,
            current_score=current_score,
            attempts=attempts,
            score_variance=variance,
            duration_minutes=duration_min,
            recommended_action=action,
            confidence=confidence,
        )
