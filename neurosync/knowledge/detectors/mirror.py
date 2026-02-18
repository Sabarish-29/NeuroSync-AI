"""
NeuroSync AI — Confidence Collapse Mirror (M09).

Detects sudden drops in mastery scores that indicate a student's confidence
is collapsing. Named "mirror" because it reflects the student's internal
state back to the system, allowing for timely emotional support.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import KNOWLEDGE_THRESHOLDS
from neurosync.core.constants import MOMENT_CONFIDENCE_COLLAPSE


@dataclass
class CollapseResult:
    """Result from the confidence collapse mirror."""
    collapse_detected: bool = False
    concept_id: str = ""
    previous_score: float = 0.0
    current_score: float = 0.0
    score_drop: float = 0.0
    recovery_target: float = 0.0
    recommended_action: str = ""
    confidence: float = 0.0


class ConfidenceCollapseMirror:
    """
    Detects confidence collapse (M09) by monitoring mastery score drops.

    A collapse is a sudden, significant drop in mastery score within a
    short time window. This often indicates the student is panicking,
    second-guessing themselves, or has encountered a topic that
    undermines their earlier understanding.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager
        self._drop_threshold = float(KNOWLEDGE_THRESHOLDS["COLLAPSE_SCORE_DROP_THRESHOLD"])
        self._window_seconds = float(KNOWLEDGE_THRESHOLDS["COLLAPSE_WINDOW_SECONDS"])
        self._recovery_target = float(KNOWLEDGE_THRESHOLDS["COLLAPSE_RECOVERY_TARGET"])
        # Track recent scores: (student_id, concept_id) -> [(timestamp, score)]
        self._score_history: dict[tuple[str, str], list[tuple[float, float]]] = {}

    def record_score(
        self,
        student_id: str,
        concept_id: str,
        score: float,
        timestamp: Optional[float] = None,
    ) -> None:
        """Record a mastery score for collapse detection."""
        key = (student_id, concept_id)
        if key not in self._score_history:
            self._score_history[key] = []
        ts = timestamp or time.time()
        self._score_history[key].append((ts, score))
        # Keep only recent history
        cutoff = ts - self._window_seconds * 2
        self._score_history[key] = [
            (t, s) for t, s in self._score_history[key] if t >= cutoff
        ]

    def detect(
        self,
        student_id: str,
        concept_id: str,
        previous_score: float,
        current_score: float,
    ) -> CollapseResult:
        """
        Detect a confidence collapse.

        Parameters
        ----------
        student_id : str
            The student.
        concept_id : str
            The concept being tracked.
        previous_score : float
            The mastery score before the latest update.
        current_score : float
            The mastery score after the latest update.
        """
        score_drop = previous_score - current_score

        if score_drop < self._drop_threshold:
            return CollapseResult(
                concept_id=concept_id,
                previous_score=previous_score,
                current_score=current_score,
                score_drop=score_drop,
            )

        # Check if the drop occurred within the time window
        key = (student_id, concept_id)
        history = self._score_history.get(key, [])
        now = time.time()

        # Check for sustained drops in the window
        recent = [(t, s) for t, s in history if t >= now - self._window_seconds]
        if recent:
            peak_in_window = max(s for _, s in recent)
            total_drop = peak_in_window - current_score
        else:
            total_drop = score_drop

        if total_drop < self._drop_threshold:
            return CollapseResult(
                concept_id=concept_id,
                previous_score=previous_score,
                current_score=current_score,
                score_drop=score_drop,
            )

        # Collapse detected
        recovery_target = max(current_score, self._recovery_target)

        # Determine action
        if total_drop > 0.5:
            action = "immediate_encouragement"
        elif total_drop > 0.35:
            action = "scaffold_review"
        else:
            action = "gentle_reassurance"

        confidence = min(1.0, 0.6 + total_drop * 0.5)

        logger.info(
            "M09 Confidence collapse: {} on {} (drop={:.2f}, {:.2f}->{:.2f})",
            student_id, concept_id, total_drop, previous_score, current_score,
        )

        return CollapseResult(
            collapse_detected=True,
            concept_id=concept_id,
            previous_score=previous_score,
            current_score=current_score,
            score_drop=total_drop,
            recovery_target=recovery_target,
            recommended_action=action,
            confidence=confidence,
        )
