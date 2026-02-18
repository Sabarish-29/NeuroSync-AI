"""
NeuroSync AI — Working Memory Overflow / Chunk Tracker (M16).

Detects when a student encounters too many new concepts in a short
time window. Based on cognitive load theory — working memory can
handle ~4 new chunks at once before performance degrades.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import KNOWLEDGE_THRESHOLDS
from neurosync.core.constants import MOMENT_WORKING_MEMORY_OVERFLOW


@dataclass
class ChunkResult:
    """Result from the chunk tracker / working memory overflow detector."""
    overflow_detected: bool = False
    new_concepts_count: int = 0
    max_allowed: int = 4
    recent_concepts: list[str] = field(default_factory=list)
    recommended_action: str = ""
    confidence: float = 0.0


class ChunkTracker:
    """
    Detects working memory overflow (M16) by tracking new concept introductions.

    Monitors how many genuinely new concepts (mastery < threshold) a student
    encounters within a sliding time window. Too many new concepts → cognitive
    overload → poor retention.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager
        self._max_new = int(KNOWLEDGE_THRESHOLDS["CHUNK_MAX_NEW_CONCEPTS"])
        self._window_minutes = float(KNOWLEDGE_THRESHOLDS["CHUNK_WINDOW_MINUTES"])
        self._new_threshold = float(KNOWLEDGE_THRESHOLDS["CHUNK_MASTERY_NEW_THRESHOLD"])
        # Track new concept encounters: student_id -> [(timestamp, concept_id)]
        self._encounters: dict[str, list[tuple[float, str]]] = {}

    def record_encounter(
        self,
        student_id: str,
        concept_id: str,
        mastery_score: float,
        timestamp: Optional[float] = None,
    ) -> None:
        """
        Record a concept encounter. Only tracks genuinely new concepts
        (below mastery threshold).
        """
        if mastery_score >= self._new_threshold:
            return  # Not a new concept

        ts = timestamp or time.time()
        if student_id not in self._encounters:
            self._encounters[student_id] = []
        self._encounters[student_id].append((ts, concept_id))

        # Clean up old entries
        cutoff = ts - self._window_minutes * 60.0
        self._encounters[student_id] = [
            (t, c) for t, c in self._encounters[student_id] if t >= cutoff
        ]

    def detect(self, student_id: str) -> ChunkResult:
        """
        Detect working memory overflow for a student.

        Checks if too many new concepts have been introduced within the
        time window.
        """
        now = time.time()
        cutoff = now - self._window_minutes * 60.0

        entries = self._encounters.get(student_id, [])
        recent = [(t, c) for t, c in entries if t >= cutoff]

        # Deduplicate concept IDs in window
        unique_concepts = list(dict.fromkeys(c for _, c in recent))
        count = len(unique_concepts)

        if count <= self._max_new:
            return ChunkResult(
                new_concepts_count=count,
                max_allowed=self._max_new,
                recent_concepts=unique_concepts,
            )

        # Overflow detected
        excess = count - self._max_new
        confidence = min(1.0, 0.6 + excess * 0.15)

        if excess >= 3:
            action = "pause_new_material"
        elif excess >= 2:
            action = "consolidation_review"
        else:
            action = "slow_down_pacing"

        logger.info(
            "M16 Working memory overflow: {} has {} new concepts (max {})",
            student_id, count, self._max_new,
        )

        return ChunkResult(
            overflow_detected=True,
            new_concepts_count=count,
            max_allowed=self._max_new,
            recent_concepts=unique_concepts,
            recommended_action=action,
            confidence=confidence,
        )
