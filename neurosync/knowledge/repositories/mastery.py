"""
NeuroSync AI — Mastery Repository.

Higher-level mastery operations that compute scores based on graph thresholds.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import KNOWLEDGE_THRESHOLDS


def _score_to_level(score: float) -> str:
    """Convert a mastery score to a level string."""
    if score >= 0.85:
        return "mastered"
    elif score >= 0.60:
        return "proficient"
    elif score >= 0.30:
        return "developing"
    return "novice"


class MasteryRepository:
    """
    High-level mastery computation using graph relationships and thresholds.

    Combines data from STUDIED relationships with threshold configuration
    to compute mastery scores, detect plateaus, and track progress.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager

    def compute_mastery_score(
        self,
        student_id: str,
        concept_id: str,
        correct: bool,
        response_time_ms: float = 0.0,
    ) -> dict[str, Any]:
        """
        Compute and update mastery score after an interaction.

        Returns dict with:
            - previous_score, new_score
            - previous_level, new_level
            - score_delta
        """
        # Get current mastery
        cypher = """
        MATCH (s:Student {student_id: $student_id})-[r:STUDIED]->(c:Concept {concept_id: $concept_id})
        RETURN r.mastery_score AS score, r.level AS level, r.attempts AS attempts
        """
        results = self._gm.execute_query(cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
        })

        if results:
            current_score = float(results[0].get("score", 0.0) or 0.0)
            current_level = str(results[0].get("level", "novice") or "novice")
        else:
            current_score = float(KNOWLEDGE_THRESHOLDS["MASTERY_INITIAL_SCORE"])
            current_level = "novice"

        # Calculate new score
        if correct:
            delta = float(KNOWLEDGE_THRESHOLDS["MASTERY_CORRECT_INCREMENT"])
            # Speed bonus
            speed_thresh = float(KNOWLEDGE_THRESHOLDS["MASTERY_SPEED_BONUS_THRESHOLD_MS"])
            if 0 < response_time_ms < speed_thresh:
                delta += float(KNOWLEDGE_THRESHOLDS["MASTERY_SPEED_BONUS"])
        else:
            delta = -float(KNOWLEDGE_THRESHOLDS["MASTERY_INCORRECT_DECREMENT"])

        max_score = float(KNOWLEDGE_THRESHOLDS["MASTERY_MAX_SCORE"])
        new_score = max(0.0, min(max_score, current_score + delta))
        new_level = _score_to_level(new_score)

        # Update in graph
        update_cypher = """
        MATCH (s:Student {student_id: $student_id})-[r:STUDIED]->(c:Concept {concept_id: $concept_id})
        SET r.mastery_score = $new_score,
            r.level = $new_level,
            r.best_score = CASE WHEN $new_score > coalesce(r.best_score, 0) THEN $new_score ELSE r.best_score END
        """
        self._gm.execute_write(update_cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
            "new_score": new_score,
            "new_level": new_level,
        })

        # Mark as mastered if threshold reached
        if new_score >= 0.85 and current_score < 0.85:
            mastered_cypher = """
            MATCH (s:Student {student_id: $student_id})
            MATCH (c:Concept {concept_id: $concept_id})
            MERGE (s)-[r:MASTERED]->(c)
            SET r.mastered_at = $now, r.score = $score
            """
            self._gm.execute_write(mastered_cypher, {
                "student_id": student_id,
                "concept_id": concept_id,
                "now": time.time(),
                "score": new_score,
            })

        return {
            "previous_score": current_score,
            "new_score": new_score,
            "previous_level": current_level,
            "new_level": new_level,
            "score_delta": new_score - current_score,
        }

    def get_prerequisite_mastery(
        self, student_id: str, concept_id: str
    ) -> list[dict[str, Any]]:
        """
        Get mastery scores for all prerequisites of a concept.

        Used by GapDetector to find knowledge gaps.
        """
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})-[:REQUIRES]->(prereq:Concept)
        OPTIONAL MATCH (s:Student {student_id: $student_id})-[r:STUDIED]->(prereq)
        RETURN prereq.concept_id AS concept_id,
               prereq.name AS concept_name,
               prereq.difficulty AS difficulty,
               coalesce(r.mastery_score, 0.0) AS mastery_score,
               coalesce(r.level, 'novice') AS level,
               coalesce(r.attempts, 0) AS attempts
        """
        return self._gm.execute_query(cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
        })

    def get_mastery_history(
        self, student_id: str, concept_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get the study history for a student-concept pair.

        Returns attempt data for plateau detection.
        """
        cypher = """
        MATCH (s:Student {student_id: $student_id})-[r:STUDIED]->(c:Concept {concept_id: $concept_id})
        RETURN r.mastery_score AS mastery_score, r.level AS level,
               r.attempts AS attempts, r.correct AS correct,
               r.incorrect AS incorrect, r.streak AS streak,
               r.first_seen AS first_seen, r.last_seen AS last_seen,
               r.best_score AS best_score
        """
        return self._gm.execute_query(cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
        })

    def get_current_segment_mastery(self, student_id: str, concept_ids: list[str]) -> float:
        """
        Compute average mastery across a set of concepts (current lesson segment).

        Used by the fusion engine to report the graph_mastery_current_segment score.
        """
        if not concept_ids:
            return 0.0

        cypher = """
        UNWIND $concept_ids AS cid
        MATCH (c:Concept {concept_id: cid})
        OPTIONAL MATCH (s:Student {student_id: $student_id})-[r:STUDIED]->(c)
        RETURN avg(coalesce(r.mastery_score, 0.0)) AS avg_mastery
        """
        results = self._gm.execute_query(cypher, {
            "student_id": student_id,
            "concept_ids": concept_ids,
        })
        if results and results[0].get("avg_mastery") is not None:
            return float(results[0]["avg_mastery"])
        return 0.0
