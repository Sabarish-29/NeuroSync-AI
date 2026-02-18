"""
NeuroSync AI — Misconception Detector (M15).

Detects when a student's wrong answers match known misconception patterns
in the knowledge graph. Provides targeted correction instead of generic
"that's wrong" feedback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import KNOWLEDGE_THRESHOLDS
from neurosync.core.constants import MOMENT_MISCONCEPTION


@dataclass
class MisconceptionResult:
    """Result from the misconception detector."""
    misconception_detected: bool = False
    concept_id: str = ""
    misconception_id: str = ""
    description: str = ""
    correction: str = ""
    severity: float = 0.0
    repeat_count: int = 0
    confidence: float = 0.0
    recommended_action: str = ""


class MisconceptionDetector:
    """
    Detects misconceptions (M15) by matching wrong answers against known patterns.

    Tracks repeat occurrences — a student giving the same wrong answer multiple
    times with confidence indicates a genuine misconception rather than a typo.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager
        self._repeat_threshold = int(KNOWLEDGE_THRESHOLDS["MISCONCEPTION_REPEAT_WRONG_THRESHOLD"])
        self._confidence_min = float(KNOWLEDGE_THRESHOLDS["MISCONCEPTION_CONFIDENCE_MIN"])
        self._penalty = float(KNOWLEDGE_THRESHOLDS["MISCONCEPTION_PENALTY_FACTOR"])
        # Track wrong answers: (student_id, concept_id, answer) -> count
        self._wrong_answer_counts: dict[tuple[str, str, str], int] = {}

    def record_wrong_answer(
        self,
        student_id: str,
        concept_id: str,
        wrong_answer: str,
    ) -> int:
        """
        Record a wrong answer and return the count for this pattern.
        """
        key = (student_id, concept_id, wrong_answer.lower().strip())
        self._wrong_answer_counts[key] = self._wrong_answer_counts.get(key, 0) + 1
        return self._wrong_answer_counts[key]

    def detect(
        self,
        student_id: str,
        concept_id: str,
        wrong_answer: str,
        student_confidence: Optional[int] = None,
        known_misconceptions: Optional[list[dict[str, Any]]] = None,
    ) -> MisconceptionResult:
        """
        Detect if a wrong answer matches a known misconception.

        Parameters
        ----------
        student_id : str
            The student who answered.
        concept_id : str
            The concept being tested.
        wrong_answer : str
            The incorrect answer given.
        student_confidence : int, optional
            Self-reported confidence (1-5).
        known_misconceptions : list[dict], optional
            Known misconceptions for this concept (from MisconceptionRepository).
            Each dict should have: misconception_id, description, common_wrong_answer,
            correction, severity.
        """
        # Track the wrong answer
        repeat_count = self.record_wrong_answer(student_id, concept_id, wrong_answer)

        if not known_misconceptions:
            # No known misconceptions to check against
            if repeat_count >= self._repeat_threshold:
                return MisconceptionResult(
                    misconception_detected=True,
                    concept_id=concept_id,
                    repeat_count=repeat_count,
                    confidence=0.5,
                    description=f"Repeated wrong answer: {wrong_answer}",
                    recommended_action="investigate_novel_misconception",
                )
            return MisconceptionResult()

        # Check against known misconceptions
        matched = None
        for mc in known_misconceptions:
            common_answer = str(mc.get("common_wrong_answer", "")).lower().strip()
            if not common_answer:
                continue
            if (wrong_answer.lower().strip() == common_answer or
                    common_answer in wrong_answer.lower().strip()):
                matched = mc
                break

        if matched is None:
            if repeat_count >= self._repeat_threshold:
                return MisconceptionResult(
                    misconception_detected=True,
                    concept_id=concept_id,
                    repeat_count=repeat_count,
                    confidence=0.4,
                    description=f"Repeated unrecognised wrong answer: {wrong_answer}",
                    recommended_action="flag_new_misconception",
                )
            return MisconceptionResult()

        # We found a matching misconception
        severity = float(matched.get("severity", 0.5))

        # Confidence calculation
        confidence = 0.6
        if repeat_count >= self._repeat_threshold:
            confidence += 0.2
        if student_confidence is not None and student_confidence >= 3:
            confidence += 0.1  # Student thinks they're right → dangerous
        confidence = min(1.0, confidence)

        # Determine action
        if repeat_count >= self._repeat_threshold and confidence > 0.7:
            action = "direct_correction"
        elif repeat_count >= self._repeat_threshold:
            action = "guided_discovery"
        else:
            action = "gentle_hint"

        logger.info(
            "M15 Misconception detected for {} on {}: {} (repeat={})",
            student_id, concept_id, matched.get("misconception_id", ""), repeat_count,
        )

        return MisconceptionResult(
            misconception_detected=True,
            concept_id=concept_id,
            misconception_id=str(matched.get("misconception_id", "")),
            description=str(matched.get("description", "")),
            correction=str(matched.get("correction", "")),
            severity=severity,
            repeat_count=repeat_count,
            confidence=confidence,
            recommended_action=action,
        )
