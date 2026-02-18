"""
NeuroSync AI — Misconception Repository.

CRUD operations for Misconception nodes and their relationships.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger


class MisconceptionRepository:
    """
    Manages Misconception nodes and HAS_MISCONCEPTION relationships.

    Misconceptions are linked to Concepts — when a student gives a wrong answer
    that matches a known misconception pattern, the system can provide targeted
    correction instead of generic feedback.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager

    def create_misconception(
        self,
        misconception_id: str,
        concept_id: str,
        description: str,
        common_wrong_answer: str = "",
        correction: str = "",
        severity: float = 0.5,
    ) -> bool:
        """Create a Misconception node and link it to a Concept."""
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})
        MERGE (m:Misconception {misconception_id: $misconception_id})
        ON CREATE SET
            m.concept_id = $concept_id,
            m.description = $description,
            m.common_wrong_answer = $common_wrong_answer,
            m.correction = $correction,
            m.severity = $severity,
            m.created_at = $created_at
        ON MATCH SET
            m.description = $description,
            m.common_wrong_answer = $common_wrong_answer,
            m.correction = $correction,
            m.severity = $severity
        MERGE (c)-[r:HAS_MISCONCEPTION]->(m)
        ON CREATE SET r.frequency = 0.0
        """
        return self._gm.execute_write(cypher, {
            "misconception_id": misconception_id,
            "concept_id": concept_id,
            "description": description,
            "common_wrong_answer": common_wrong_answer,
            "correction": correction,
            "severity": severity,
            "created_at": time.time(),
        })

    def get_misconceptions_for_concept(self, concept_id: str) -> list[dict[str, Any]]:
        """Get all misconceptions linked to a concept."""
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})-[r:HAS_MISCONCEPTION]->(m:Misconception)
        RETURN m.misconception_id AS misconception_id,
               m.description AS description,
               m.common_wrong_answer AS common_wrong_answer,
               m.correction AS correction,
               m.severity AS severity,
               r.frequency AS frequency
        ORDER BY m.severity DESC
        """
        return self._gm.execute_query(cypher, {"concept_id": concept_id})

    def get_misconception(self, misconception_id: str) -> Optional[dict[str, Any]]:
        """Get a misconception by ID."""
        cypher = """
        MATCH (m:Misconception {misconception_id: $misconception_id})
        RETURN m.misconception_id AS misconception_id,
               m.concept_id AS concept_id,
               m.description AS description,
               m.common_wrong_answer AS common_wrong_answer,
               m.correction AS correction,
               m.severity AS severity
        """
        results = self._gm.execute_query(cypher, {"misconception_id": misconception_id})
        return results[0] if results else None

    def match_wrong_answer(
        self, concept_id: str, wrong_answer: str
    ) -> Optional[dict[str, Any]]:
        """
        Check if a wrong answer matches a known misconception pattern.

        Uses case-insensitive CONTAINS matching.
        """
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})-[:HAS_MISCONCEPTION]->(m:Misconception)
        WHERE toLower(m.common_wrong_answer) = toLower($wrong_answer)
           OR toLower($wrong_answer) CONTAINS toLower(m.common_wrong_answer)
        RETURN m.misconception_id AS misconception_id,
               m.description AS description,
               m.correction AS correction,
               m.severity AS severity
        LIMIT 1
        """
        results = self._gm.execute_query(cypher, {
            "concept_id": concept_id,
            "wrong_answer": wrong_answer,
        })
        return results[0] if results else None

    def increment_frequency(self, concept_id: str, misconception_id: str) -> bool:
        """Increment the frequency counter for a misconception relationship."""
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})-[r:HAS_MISCONCEPTION]->(m:Misconception {misconception_id: $misconception_id})
        SET r.frequency = coalesce(r.frequency, 0.0) + 1.0
        """
        return self._gm.execute_write(cypher, {
            "concept_id": concept_id,
            "misconception_id": misconception_id,
        })
