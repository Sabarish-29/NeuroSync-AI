"""
NeuroSync AI — Mastery Checker (M06 — Stealth Boredom).

Detects when a student has already mastered material and is being made to
repeat it. This creates "stealth boredom" — the student appears engaged
but is actually under-challenged and disengaging internally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import KNOWLEDGE_THRESHOLDS
from neurosync.core.constants import MOMENT_STEALTH_BOREDOM


@dataclass
class BoredomResult:
    """Result from the stealth boredom / mastery checker."""
    boredom_detected: bool = False
    concept_id: str = ""
    mastery_score: float = 0.0
    repeat_count: int = 0
    recommended_next_concepts: list[str] = field(default_factory=list)
    recommended_action: str = ""
    confidence: float = 0.0


class MasteryChecker:
    """
    Detects stealth boredom (M06) by identifying over-mastered concepts.

    When a student has high mastery on a concept but keeps encountering it,
    they need to be advanced to harder material.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager
        self._mastery_ceiling = float(KNOWLEDGE_THRESHOLDS["BOREDOM_MASTERY_CEILING"])
        self._repeat_threshold = int(KNOWLEDGE_THRESHOLDS["BOREDOM_REPEAT_THRESHOLD"])
        self._advance_score = float(KNOWLEDGE_THRESHOLDS["BOREDOM_ADVANCE_SCORE"])
        # Track encounter counts per concept per student
        self._encounter_counts: dict[tuple[str, str], int] = {}

    def record_encounter(self, student_id: str, concept_id: str) -> int:
        """Record that a student encountered a concept. Returns the total count."""
        key = (student_id, concept_id)
        self._encounter_counts[key] = self._encounter_counts.get(key, 0) + 1
        return self._encounter_counts[key]

    def detect(
        self,
        student_id: str,
        concept_id: str,
        mastery_score: float,
        next_concepts: Optional[list[dict[str, Any]]] = None,
    ) -> BoredomResult:
        """
        Detect stealth boredom for a student on a concept.

        Parameters
        ----------
        student_id : str
            The student.
        concept_id : str
            The concept to check.
        mastery_score : float
            Current mastery score for this concept.
        next_concepts : list[dict], optional
            Possible next concepts from the graph (from ConceptRepository.get_next_concepts()).
        """
        encounter_count = self._encounter_counts.get((student_id, concept_id), 0)

        # Not bored if mastery is below ceiling or not enough repeats
        if mastery_score < self._mastery_ceiling:
            return BoredomResult(concept_id=concept_id, mastery_score=mastery_score)

        if encounter_count < self._repeat_threshold:
            return BoredomResult(
                concept_id=concept_id,
                mastery_score=mastery_score,
                repeat_count=encounter_count,
            )

        # Boredom detected: student has mastered this and keeps seeing it
        next_ids = []
        if next_concepts:
            next_ids = [str(nc.get("concept_id", "")) for nc in next_concepts]

        # Confidence scales with how over-mastered and over-repeated
        excess_mastery = mastery_score - self._mastery_ceiling
        excess_repeats = encounter_count - self._repeat_threshold
        confidence = min(1.0, 0.6 + excess_mastery * 0.5 + min(excess_repeats * 0.05, 0.2))

        action = "advance_to_next" if next_ids else "increase_difficulty"

        logger.info(
            "M06 Stealth boredom: {} on {} (mastery={:.2f}, repeats={})",
            student_id, concept_id, mastery_score, encounter_count,
        )

        return BoredomResult(
            boredom_detected=True,
            concept_id=concept_id,
            mastery_score=mastery_score,
            repeat_count=encounter_count,
            recommended_next_concepts=next_ids,
            recommended_action=action,
            confidence=confidence,
        )
