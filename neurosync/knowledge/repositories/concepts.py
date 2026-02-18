"""
NeuroSync AI — Concept Repository.

CRUD operations for Concept nodes in the knowledge graph.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger


class ConceptRepository:
    """
    Manages Concept nodes in Neo4j.

    All methods accept a graph_manager instance and use parameterised Cypher.
    Returns safe defaults when the graph is offline.
    """

    def __init__(self, graph_manager: Any) -> None:
        self._gm = graph_manager

    def create_concept(
        self,
        concept_id: str,
        name: str,
        category: str = "core",
        difficulty: float = 0.5,
        description: str = "",
        subject: str = "",
    ) -> bool:
        """Create a Concept node. Returns True on success."""
        cypher = """
        MERGE (c:Concept {concept_id: $concept_id})
        ON CREATE SET
            c.name = $name,
            c.category = $category,
            c.difficulty = $difficulty,
            c.description = $description,
            c.subject = $subject,
            c.created_at = $created_at
        ON MATCH SET
            c.name = $name,
            c.category = $category,
            c.difficulty = $difficulty,
            c.description = $description,
            c.subject = $subject
        """
        return self._gm.execute_write(cypher, {
            "concept_id": concept_id,
            "name": name,
            "category": category,
            "difficulty": difficulty,
            "description": description,
            "subject": subject,
            "created_at": time.time(),
        })

    def get_concept(self, concept_id: str) -> Optional[dict[str, Any]]:
        """Get a concept by ID. Returns None if not found."""
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})
        RETURN c.concept_id AS concept_id, c.name AS name,
               c.category AS category, c.difficulty AS difficulty,
               c.description AS description, c.subject AS subject
        """
        results = self._gm.execute_query(cypher, {"concept_id": concept_id})
        return results[0] if results else None

    def get_all_concepts(self, subject: Optional[str] = None) -> list[dict[str, Any]]:
        """Get all concepts, optionally filtered by subject."""
        if subject:
            cypher = """
            MATCH (c:Concept)
            WHERE c.subject = $subject
            RETURN c.concept_id AS concept_id, c.name AS name,
                   c.category AS category, c.difficulty AS difficulty,
                   c.subject AS subject
            ORDER BY c.difficulty
            """
            return self._gm.execute_query(cypher, {"subject": subject})

        cypher = """
        MATCH (c:Concept)
        RETURN c.concept_id AS concept_id, c.name AS name,
               c.category AS category, c.difficulty AS difficulty,
               c.subject AS subject
        ORDER BY c.difficulty
        """
        return self._gm.execute_query(cypher)

    def get_prerequisites(self, concept_id: str) -> list[dict[str, Any]]:
        """Get all prerequisite concepts for a given concept."""
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})-[:REQUIRES]->(prereq:Concept)
        RETURN prereq.concept_id AS concept_id, prereq.name AS name,
               prereq.category AS category, prereq.difficulty AS difficulty
        """
        return self._gm.execute_query(cypher, {"concept_id": concept_id})

    def get_dependents(self, concept_id: str) -> list[dict[str, Any]]:
        """Get all concepts that depend on the given concept."""
        cypher = """
        MATCH (dependent:Concept)-[:REQUIRES]->(c:Concept {concept_id: $concept_id})
        RETURN dependent.concept_id AS concept_id, dependent.name AS name,
               dependent.category AS category, dependent.difficulty AS difficulty
        """
        return self._gm.execute_query(cypher, {"concept_id": concept_id})

    def add_prerequisite(
        self,
        concept_id: str,
        prerequisite_id: str,
        weight: float = 1.0,
        description: str = "",
    ) -> bool:
        """Create a REQUIRES relationship between two concepts."""
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})
        MATCH (prereq:Concept {concept_id: $prerequisite_id})
        MERGE (c)-[r:REQUIRES]->(prereq)
        SET r.weight = $weight, r.description = $description
        """
        return self._gm.execute_write(cypher, {
            "concept_id": concept_id,
            "prerequisite_id": prerequisite_id,
            "weight": weight,
            "description": description,
        })

    def add_next_concept(
        self,
        concept_id: str,
        next_concept_id: str,
        suggested_order: int = 1,
    ) -> bool:
        """Create a NEXT_CONCEPT relationship for learning path ordering."""
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})
        MATCH (next:Concept {concept_id: $next_concept_id})
        MERGE (c)-[r:NEXT_CONCEPT]->(next)
        SET r.suggested_order = $suggested_order
        """
        return self._gm.execute_write(cypher, {
            "concept_id": concept_id,
            "next_concept_id": next_concept_id,
            "suggested_order": suggested_order,
        })

    def get_next_concepts(self, concept_id: str) -> list[dict[str, Any]]:
        """Get next concepts in the learning path."""
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id})-[r:NEXT_CONCEPT]->(next:Concept)
        RETURN next.concept_id AS concept_id, next.name AS name,
               next.difficulty AS difficulty, r.suggested_order AS order
        ORDER BY r.suggested_order
        """
        return self._gm.execute_query(cypher, {"concept_id": concept_id})
