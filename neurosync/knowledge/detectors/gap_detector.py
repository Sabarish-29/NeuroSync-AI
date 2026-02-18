"""
NeuroSync AI — Knowledge Gap Detector (M03).

Detects when a student is struggling with a concept because they lack
mastery of prerequisite concepts. Queries the knowledge graph to find
which prerequisites are weak and recommends remediation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import KNOWLEDGE_THRESHOLDS
from neurosync.core.constants import MOMENT_KNOWLEDGE_GAP


@dataclass
class GapResult:
    """Result from the knowledge gap detector."""
    gap_detected: bool = False
    concept_id: str = ""
    weak_prerequisites: list[dict[str, Any]] = field(default_factory=list)
    strongest_gap: str = ""
    gap_severity: float = 0.0
    recommended_action: str = ""
    confidence: float = 0.0


class GapDetector:
    """
    Detects knowledge gaps (M03) by checking prerequisite mastery.

    When a student fails at a concept, this detector checks the graph for
    prerequisite concepts with low mastery scores, indicating the student
    is missing foundational knowledge.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager
        self._min_mastery = float(KNOWLEDGE_THRESHOLDS["GAP_PREREQUISITE_MASTERY_MIN"])
        self._failure_streak = int(KNOWLEDGE_THRESHOLDS["GAP_FAILURE_STREAK_TRIGGER"])
        self._consecutive_failures: dict[str, int] = {}  # concept_id -> count

    def record_attempt(self, concept_id: str, correct: bool) -> None:
        """Track consecutive failures per concept."""
        if correct:
            self._consecutive_failures[concept_id] = 0
        else:
            self._consecutive_failures[concept_id] = (
                self._consecutive_failures.get(concept_id, 0) + 1
            )

    def detect(
        self,
        student_id: str,
        concept_id: str,
        prerequisite_mastery: list[dict[str, Any]],
    ) -> GapResult:
        """
        Detect knowledge gaps based on prerequisite mastery data.

        Parameters
        ----------
        student_id : str
            The student being checked.
        concept_id : str
            The concept the student is currently working on.
        prerequisite_mastery : list[dict]
            List of dicts with keys: concept_id, concept_name, mastery_score, level.
            This data comes from MasteryRepository.get_prerequisite_mastery().
        """
        if not prerequisite_mastery:
            return GapResult()

        # Find weak prerequisites
        weak = []
        for prereq in prerequisite_mastery:
            score = float(prereq.get("mastery_score", 0.0) or 0.0)
            if score < self._min_mastery:
                weak.append(prereq)

        if not weak:
            return GapResult()

        # Sort by mastery (lowest first)
        weak.sort(key=lambda p: float(p.get("mastery_score", 0.0) or 0.0))
        strongest_gap = weak[0]

        # Calculate severity (0-1): more weak prereqs and lower scores = more severe
        avg_mastery = sum(float(p.get("mastery_score", 0.0) or 0.0) for p in weak) / len(weak)
        severity = min(1.0, (1.0 - avg_mastery) * (len(weak) / max(len(prerequisite_mastery), 1)))

        # Check failure streak for confidence boost
        failures = self._consecutive_failures.get(concept_id, 0)
        streak_factor = min(1.0, failures / self._failure_streak) if failures > 0 else 0.0
        confidence = min(1.0, 0.5 + severity * 0.3 + streak_factor * 0.2)

        # Determine recommended action
        if severity > 0.7:
            action = f"redirect_to_prerequisite:{strongest_gap.get('concept_id', '')}"
        elif severity > 0.4:
            action = f"review_prerequisite:{strongest_gap.get('concept_id', '')}"
        else:
            action = f"hint_prerequisite:{strongest_gap.get('concept_id', '')}"

        logger.info(
            "M03 Gap detected for {} on concept {}: {} weak prereqs, severity={:.2f}",
            student_id, concept_id, len(weak), severity,
        )

        return GapResult(
            gap_detected=True,
            concept_id=concept_id,
            weak_prerequisites=weak,
            strongest_gap=str(strongest_gap.get("concept_id", "")),
            gap_severity=severity,
            recommended_action=action,
            confidence=confidence,
        )
