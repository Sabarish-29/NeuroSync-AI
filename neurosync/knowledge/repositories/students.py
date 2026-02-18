"""
NeuroSync AI — Student Repository.

CRUD operations for Student nodes and their relationships in the knowledge graph.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger


class StudentRepository:
    """
    Manages Student nodes and STUDIED/MASTERED/STRUGGLES_WITH relationships.

    All methods use parameterised Cypher and return safe defaults when offline.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager

    def create_student(self, student_id: str, name: str = "") -> bool:
        """Create or update a Student node."""
        cypher = """
        MERGE (s:Student {student_id: $student_id})
        ON CREATE SET s.name = $name, s.created_at = $created_at
        ON MATCH SET s.name = $name
        """
        return self._gm.execute_write(cypher, {
            "student_id": student_id,
            "name": name or student_id,
            "created_at": time.time(),
        })

    def get_student(self, student_id: str) -> Optional[dict[str, Any]]:
        """Get a student by ID."""
        cypher = """
        MATCH (s:Student {student_id: $student_id})
        RETURN s.student_id AS student_id, s.name AS name, s.created_at AS created_at
        """
        results = self._gm.execute_query(cypher, {"student_id": student_id})
        return results[0] if results else None

    def record_study(
        self,
        student_id: str,
        concept_id: str,
        correct: bool,
        response_time_ms: float = 0.0,
    ) -> bool:
        """
        Record that a student studied a concept (answered a question).

        Updates the STUDIED relationship with running statistics.
        """
        now = time.time()
        cypher = """
        MATCH (s:Student {student_id: $student_id})
        MATCH (c:Concept {concept_id: $concept_id})
        MERGE (s)-[r:STUDIED]->(c)
        ON CREATE SET
            r.mastery_score = $initial_score,
            r.level = 'novice',
            r.attempts = 1,
            r.correct = CASE WHEN $correct THEN 1 ELSE 0 END,
            r.incorrect = CASE WHEN $correct THEN 0 ELSE 1 END,
            r.first_seen = $now,
            r.last_seen = $now,
            r.streak = CASE WHEN $correct THEN 1 ELSE 0 END,
            r.best_score = $initial_score
        ON MATCH SET
            r.attempts = r.attempts + 1,
            r.correct = r.correct + CASE WHEN $correct THEN 1 ELSE 0 END,
            r.incorrect = r.incorrect + CASE WHEN $correct THEN 0 ELSE 1 END,
            r.last_seen = $now,
            r.streak = CASE WHEN $correct THEN r.streak + 1 ELSE 0 END
        """
        return self._gm.execute_write(cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
            "correct": correct,
            "now": now,
            "initial_score": 0.15 if correct else 0.0,
        })

    def update_mastery(
        self,
        student_id: str,
        concept_id: str,
        new_score: float,
        level: str,
    ) -> bool:
        """Update the mastery score and level on a STUDIED relationship."""
        cypher = """
        MATCH (s:Student {student_id: $student_id})-[r:STUDIED]->(c:Concept {concept_id: $concept_id})
        SET r.mastery_score = $new_score,
            r.level = $level,
            r.best_score = CASE WHEN $new_score > coalesce(r.best_score, 0) THEN $new_score ELSE r.best_score END
        """
        return self._gm.execute_write(cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
            "new_score": new_score,
            "level": level,
        })

    def mark_mastered(self, student_id: str, concept_id: str, score: float) -> bool:
        """Create a MASTERED relationship when a student masters a concept."""
        cypher = """
        MATCH (s:Student {student_id: $student_id})
        MATCH (c:Concept {concept_id: $concept_id})
        MERGE (s)-[r:MASTERED]->(c)
        SET r.mastered_at = $now, r.score = $score
        """
        return self._gm.execute_write(cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
            "now": time.time(),
            "score": score,
        })

    def mark_struggle(self, student_id: str, concept_id: str) -> bool:
        """Create/update a STRUGGLES_WITH relationship."""
        cypher = """
        MATCH (s:Student {student_id: $student_id})
        MATCH (c:Concept {concept_id: $concept_id})
        MERGE (s)-[r:STRUGGLES_WITH]->(c)
        ON CREATE SET r.failure_count = 1, r.last_failure = $now
        ON MATCH SET r.failure_count = r.failure_count + 1, r.last_failure = $now
        """
        return self._gm.execute_write(cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
            "now": time.time(),
        })

    def get_mastery(self, student_id: str, concept_id: str) -> Optional[dict[str, Any]]:
        """Get the mastery data for a student-concept pair."""
        cypher = """
        MATCH (s:Student {student_id: $student_id})-[r:STUDIED]->(c:Concept {concept_id: $concept_id})
        RETURN r.mastery_score AS mastery_score, r.level AS level,
               r.attempts AS attempts, r.correct AS correct,
               r.incorrect AS incorrect, r.streak AS streak,
               r.first_seen AS first_seen, r.last_seen AS last_seen,
               r.best_score AS best_score
        """
        results = self._gm.execute_query(cypher, {
            "student_id": student_id,
            "concept_id": concept_id,
        })
        return results[0] if results else None

    def get_all_mastery(self, student_id: str) -> list[dict[str, Any]]:
        """Get mastery data for all concepts a student has studied."""
        cypher = """
        MATCH (s:Student {student_id: $student_id})-[r:STUDIED]->(c:Concept)
        RETURN c.concept_id AS concept_id, c.name AS concept_name,
               r.mastery_score AS mastery_score, r.level AS level,
               r.attempts AS attempts, r.correct AS correct, r.streak AS streak
        ORDER BY r.mastery_score DESC
        """
        return self._gm.execute_query(cypher, {"student_id": student_id})

    def get_struggles(self, student_id: str) -> list[dict[str, Any]]:
        """Get all concepts a student is struggling with."""
        cypher = """
        MATCH (s:Student {student_id: $student_id})-[r:STRUGGLES_WITH]->(c:Concept)
        RETURN c.concept_id AS concept_id, c.name AS concept_name,
               r.failure_count AS failure_count, r.last_failure AS last_failure
        ORDER BY r.failure_count DESC
        """
        return self._gm.execute_query(cypher, {"student_id": student_id})

    def get_mastered_concepts(self, student_id: str) -> list[dict[str, Any]]:
        """Get all concepts a student has mastered."""
        cypher = """
        MATCH (s:Student {student_id: $student_id})-[r:MASTERED]->(c:Concept)
        RETURN c.concept_id AS concept_id, c.name AS concept_name,
               r.mastered_at AS mastered_at, r.score AS score
        ORDER BY r.mastered_at DESC
        """
        return self._gm.execute_query(cypher, {"student_id": student_id})
