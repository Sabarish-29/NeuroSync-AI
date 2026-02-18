"""
NeuroSync AI — Knowledge Graph test fixtures.

Provides a MockGraphManager that uses Python dicts instead of Neo4j,
allowing all 25 graph tests to run without a Neo4j instance.
"""

from __future__ import annotations

import copy
import re
import time
from typing import Any, Optional

import pytest


# =============================================================================
# MockGraphManager — in-memory dict-based Neo4j mock
# =============================================================================

class MockGraphManager:
    """
    In-memory mock of GraphManager that stores nodes and relationships
    in Python dicts.  Supports a subset of Cypher via pattern matching
    on the query strings — enough for the repository tests.

    Usage:
        gm = MockGraphManager()
        gm.connect()  # always returns True
    """

    def __init__(self) -> None:
        self._connected = True
        # Storage: label -> {id -> properties}
        self._nodes: dict[str, dict[str, dict[str, Any]]] = {
            "Concept": {},
            "Student": {},
            "Misconception": {},
        }
        # Relationships: (from_label, from_id, rel_type, to_label, to_id) -> properties
        self._rels: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def driver(self) -> None:
        return None

    def connect(self) -> bool:
        self._connected = True
        return True

    def close(self) -> None:
        self._connected = False

    def session(self, **kwargs: Any) -> Any:
        return self

    def __enter__(self) -> MockGraphManager:
        return self

    def __exit__(self, *_: Any) -> None:
        pass

    # -----------------------------------------------------------------
    # Query execution — pattern-matches Cypher and dispatches
    # -----------------------------------------------------------------

    def execute_query(
        self, cypher: str, parameters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """Execute a read query and return results."""
        if not self._connected:
            return []
        params = parameters or {}
        return self._dispatch(cypher, params, write=False)

    def execute_write(
        self, cypher: str, parameters: Optional[dict[str, Any]] = None
    ) -> bool:
        """Execute a write query and return True on success."""
        if not self._connected:
            return False
        params = parameters or {}
        self._dispatch(cypher, params, write=True)
        return True

    # -----------------------------------------------------------------
    # Internal Cypher dispatcher
    # -----------------------------------------------------------------

    def _dispatch(
        self, cypher: str, params: dict[str, Any], write: bool
    ) -> list[dict[str, Any]]:
        """Route Cypher to the appropriate handler based on patterns.

        IMPORTANT: More specific patterns must be checked before generic ones.
        Relationship queries must be checked before single-node queries,
        because relationship queries also contain node match patterns.
        """
        c = cypher.strip().upper()

        if write:
            return self._dispatch_write(c, params)
        return self._dispatch_read(c, params)

    def _dispatch_write(
        self, c: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Handle all write (MERGE/SET) queries."""

        # STUDIED relationship (MERGE)
        if "MERGE (S)-[R:STUDIED]->(C)" in c:
            return self._merge_studied(params)

        # Update mastery on STUDIED (SET without MERGE on the rel)
        if "SET R.MASTERY_SCORE" in c and "STUDIED" in c:
            return self._update_mastery(params)

        # REQUIRES relationship
        if "REQUIRES" in c and "MERGE" in c:
            self._add_relationship("Concept", params.get("concept_id", ""),
                                   "REQUIRES", "Concept", params.get("prerequisite_id", ""),
                                   {"weight": params.get("weight", 1.0),
                                    "description": params.get("description", "")})
            return []

        # NEXT_CONCEPT relationship
        if "NEXT_CONCEPT" in c and "MERGE" in c:
            self._add_relationship("Concept", params.get("concept_id", ""),
                                   "NEXT_CONCEPT", "Concept", params.get("next_concept_id", ""),
                                   {"suggested_order": params.get("suggested_order", 1)})
            return []

        # MASTERED relationship
        if "MASTERED" in c and "MERGE" in c:
            self._add_relationship("Student", params.get("student_id", ""),
                                   "MASTERED", "Concept", params.get("concept_id", ""),
                                   {"mastered_at": params.get("now", time.time()),
                                    "score": params.get("score", 0.0)})
            return []

        # STRUGGLES_WITH relationship
        if "STRUGGLES_WITH" in c and "MERGE" in c:
            return self._merge_struggles(params)

        # HAS_MISCONCEPTION frequency update (SET without MERGE on misconception)
        if "HAS_MISCONCEPTION" in c and "COALESCE(R.FREQUENCY" in c:
            key = ("Concept", params.get("concept_id", ""),
                   "HAS_MISCONCEPTION", "Misconception", params.get("misconception_id", ""))
            if key in self._rels:
                self._rels[key]["frequency"] = self._rels[key].get("frequency", 0.0) + 1.0
            return []

        # MERGE Misconception (also creates HAS_MISCONCEPTION rel)
        if "MERGE (M:MISCONCEPTION" in c:
            self._merge_misconception(params)
            return []

        # MERGE Concept
        if "MERGE (C:CONCEPT" in c:
            self._merge_concept(params)
            return []

        # MERGE Student
        if "MERGE (S:STUDENT" in c:
            self._merge_student(params)
            return []

        return []

    def _dispatch_read(
        self, c: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Handle all read queries.

        Order: most specific (multi-keyword) patterns first,
        then generic single-node patterns last.
        """

        # 1. UNWIND (segment mastery) — very specific keyword
        if "UNWIND" in c:
            return self._segment_mastery(params)

        # 2. Match wrong answer (TOLOWER + HAS_MISCONCEPTION)
        if "TOLOWER" in c and "HAS_MISCONCEPTION" in c:
            return self._match_wrong_answer(params)

        # 3. Prerequisite mastery (has BOTH REQUIRES and STUDIED)
        if "REQUIRES" in c and "STUDIED" in c:
            return self._get_prerequisite_mastery(params)

        # 4. Prerequisites (REQUIRES → prereq concept)
        if "REQUIRES" in c and "PREREQ" in c:
            return self._get_prerequisites(params.get("concept_id", ""))

        # 5. Dependents (other concept REQUIRES this one)
        if "REQUIRES" in c and "DEPENDENT" in c:
            return self._get_dependents(params.get("concept_id", ""))

        # 6. Next concepts in learning path
        if "NEXT_CONCEPT" in c:
            return self._get_next_concepts(params.get("concept_id", ""))

        # 7. Misconceptions for a concept
        if "HAS_MISCONCEPTION" in c:
            return self._get_misconceptions(params)

        # 8. Struggles
        if "STRUGGLES_WITH" in c:
            return self._get_struggles(params)

        # 9. STUDIED relationships (mastery data)
        if "STUDIED" in c:
            return self._get_studied(params)

        # 10. MASTERED concepts
        if "MASTERED" in c:
            return self._get_mastered(params)

        # 11. Single misconception by ID
        if "MISCONCEPTION" in c and params.get("misconception_id"):
            mid = params["misconception_id"]
            mc = self._nodes["Misconception"].get(mid)
            if mc:
                return [mc.copy()]
            return []

        # 12. All concepts (query has "MATCH (C:CONCEPT)" with closing paren)
        if "MATCH (C:CONCEPT)" in c:
            subject = params.get("subject")
            results = []
            for props in self._nodes["Concept"].values():
                if subject and props.get("subject") != subject:
                    continue
                results.append(props.copy())
            results.sort(key=lambda x: x.get("difficulty", 0))
            return results

        # 13. Single concept by concept_id param
        if params.get("concept_id") and "CONCEPT" in c:
            cid = params["concept_id"]
            concept = self._nodes["Concept"].get(cid)
            if concept:
                return [concept.copy()]
            return []

        # 14. Single student by student_id param
        if params.get("student_id") and "STUDENT" in c:
            sid = params["student_id"]
            student = self._nodes["Student"].get(sid)
            if student:
                return [student.copy()]
            return []

        return []

    # -----------------------------------------------------------------
    # Write helpers
    # -----------------------------------------------------------------

    def _merge_concept(self, params: dict[str, Any]) -> None:
        cid = params["concept_id"]
        self._nodes["Concept"][cid] = {
            "concept_id": cid,
            "name": params.get("name", ""),
            "category": params.get("category", "core"),
            "difficulty": params.get("difficulty", 0.5),
            "description": params.get("description", ""),
            "subject": params.get("subject", ""),
        }

    def _merge_student(self, params: dict[str, Any]) -> None:
        sid = params["student_id"]
        self._nodes["Student"][sid] = {
            "student_id": sid,
            "name": params.get("name", sid),
            "created_at": params.get("created_at", time.time()),
        }

    def _merge_misconception(self, params: dict[str, Any]) -> None:
        mid = params["misconception_id"]
        cid = params.get("concept_id", "")
        self._nodes["Misconception"][mid] = {
            "misconception_id": mid,
            "concept_id": cid,
            "description": params.get("description", ""),
            "common_wrong_answer": params.get("common_wrong_answer", ""),
            "correction": params.get("correction", ""),
            "severity": params.get("severity", 0.5),
        }
        # Also create HAS_MISCONCEPTION relationship
        self._add_relationship("Concept", cid, "HAS_MISCONCEPTION", "Misconception", mid,
                               {"frequency": 0.0})

    def _add_relationship(
        self, from_label: str, from_id: str,
        rel_type: str,
        to_label: str, to_id: str,
        properties: dict[str, Any],
    ) -> None:
        key = (from_label, from_id, rel_type, to_label, to_id)
        if key in self._rels:
            self._rels[key].update(properties)
        else:
            self._rels[key] = properties.copy()

    def _merge_studied(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        sid = params.get("student_id", "")
        cid = params.get("concept_id", "")
        correct = params.get("correct", False)
        now = params.get("now", time.time())
        key = ("Student", sid, "STUDIED", "Concept", cid)

        if key in self._rels:
            rel = self._rels[key]
            rel["attempts"] = rel.get("attempts", 0) + 1
            if correct:
                rel["correct"] = rel.get("correct", 0) + 1
                rel["streak"] = rel.get("streak", 0) + 1
            else:
                rel["incorrect"] = rel.get("incorrect", 0) + 1
                rel["streak"] = 0
            rel["last_seen"] = now
        else:
            self._rels[key] = {
                "mastery_score": params.get("initial_score", 0.0),
                "level": "novice",
                "attempts": 1,
                "correct": 1 if correct else 0,
                "incorrect": 0 if correct else 1,
                "first_seen": now,
                "last_seen": now,
                "streak": 1 if correct else 0,
                "best_score": params.get("initial_score", 0.0),
            }
        return []

    def _update_mastery(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        sid = params.get("student_id", "")
        cid = params.get("concept_id", "")
        key = ("Student", sid, "STUDIED", "Concept", cid)
        if key in self._rels:
            new_score = params.get("new_score", 0.0)
            self._rels[key]["mastery_score"] = new_score
            self._rels[key]["level"] = params.get("new_level", params.get("level", "novice"))
            if new_score > self._rels[key].get("best_score", 0):
                self._rels[key]["best_score"] = new_score
        return []

    def _merge_struggles(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        sid = params.get("student_id", "")
        cid = params.get("concept_id", "")
        key = ("Student", sid, "STRUGGLES_WITH", "Concept", cid)
        if key in self._rels:
            self._rels[key]["failure_count"] = self._rels[key].get("failure_count", 0) + 1
            self._rels[key]["last_failure"] = params.get("now", time.time())
        else:
            self._rels[key] = {
                "failure_count": 1,
                "last_failure": params.get("now", time.time()),
            }
        return []

    # -----------------------------------------------------------------
    # Read helpers
    # -----------------------------------------------------------------

    def _get_prerequisites(self, concept_id: str) -> list[dict[str, Any]]:
        results = []
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if fl == "Concept" and fid == concept_id and rt == "REQUIRES" and tl == "Concept":
                concept = self._nodes["Concept"].get(tid)
                if concept:
                    results.append(concept.copy())
        return results

    def _get_dependents(self, concept_id: str) -> list[dict[str, Any]]:
        results = []
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if tl == "Concept" and tid == concept_id and rt == "REQUIRES" and fl == "Concept":
                concept = self._nodes["Concept"].get(fid)
                if concept:
                    results.append(concept.copy())
        return results

    def _get_next_concepts(self, concept_id: str) -> list[dict[str, Any]]:
        results = []
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if fl == "Concept" and fid == concept_id and rt == "NEXT_CONCEPT" and tl == "Concept":
                concept = self._nodes["Concept"].get(tid)
                if concept:
                    result = concept.copy()
                    result["order"] = props.get("suggested_order", 1)
                    results.append(result)
        results.sort(key=lambda x: x.get("order", 1))
        return results

    def _get_studied(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        sid = params.get("student_id", "")
        cid = params.get("concept_id")
        concept_ids = params.get("concept_ids")  # for unwind queries

        if cid:
            # Single concept
            key = ("Student", sid, "STUDIED", "Concept", cid)
            rel = self._rels.get(key)
            if rel:
                result = rel.copy()
                # Add common aliases used by different Cypher RETURN clauses
                result["score"] = result.get("mastery_score", 0.0)
                return [result]
            return []

        # All studied concepts
        results = []
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if fl == "Student" and fid == sid and rt == "STUDIED" and tl == "Concept":
                concept = self._nodes["Concept"].get(tid, {})
                result = props.copy()
                result["concept_id"] = tid
                result["concept_name"] = concept.get("name", "")
                result["score"] = result.get("mastery_score", 0.0)
                results.append(result)
        results.sort(key=lambda x: x.get("mastery_score", 0), reverse=True)
        return results

    def _get_prerequisite_mastery(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Handle prerequisite mastery query (has both REQUIRES and STUDIED)."""
        concept_id = params.get("concept_id", "")
        student_id = params.get("student_id", "")
        results = []
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if fl == "Concept" and fid == concept_id and rt == "REQUIRES" and tl == "Concept":
                prereq = self._nodes["Concept"].get(tid, {})
                studied_key = ("Student", student_id, "STUDIED", "Concept", tid)
                studied = self._rels.get(studied_key, {})
                result = {
                    "concept_id": tid,
                    "concept_name": prereq.get("name", ""),
                    "difficulty": prereq.get("difficulty", 0.5),
                    "mastery_score": float(studied.get("mastery_score", 0.0)),
                    "level": studied.get("level", "novice"),
                    "attempts": int(studied.get("attempts", 0)),
                }
                results.append(result)
        return results

    def _get_misconceptions(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        cid = params.get("concept_id", "")
        results = []
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if fl == "Concept" and fid == cid and rt == "HAS_MISCONCEPTION" and tl == "Misconception":
                mc = self._nodes["Misconception"].get(tid)
                if mc:
                    result = mc.copy()
                    result["frequency"] = props.get("frequency", 0.0)
                    results.append(result)
        return results

    def _match_wrong_answer(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        cid = params.get("concept_id", "")
        wrong = params.get("wrong_answer", "").lower().strip()
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if fl == "Concept" and fid == cid and rt == "HAS_MISCONCEPTION" and tl == "Misconception":
                mc = self._nodes["Misconception"].get(tid)
                if mc:
                    common = str(mc.get("common_wrong_answer", "")).lower().strip()
                    if common and (common == wrong or common in wrong):
                        return [mc.copy()]
        return []

    def _get_struggles(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        sid = params.get("student_id", "")
        results = []
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if fl == "Student" and fid == sid and rt == "STRUGGLES_WITH" and tl == "Concept":
                concept = self._nodes["Concept"].get(tid, {})
                result = props.copy()
                result["concept_id"] = tid
                result["concept_name"] = concept.get("name", "")
                results.append(result)
        return results

    def _get_mastered(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        sid = params.get("student_id", "")
        results = []
        for (fl, fid, rt, tl, tid), props in self._rels.items():
            if fl == "Student" and fid == sid and rt == "MASTERED" and tl == "Concept":
                concept = self._nodes["Concept"].get(tid, {})
                result = props.copy()
                result["concept_id"] = tid
                result["concept_name"] = concept.get("name", "")
                results.append(result)
        return results

    def _segment_mastery(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        sid = params.get("student_id", "")
        concept_ids = params.get("concept_ids", [])
        if not concept_ids:
            return [{"avg_mastery": 0.0}]

        scores = []
        for cid in concept_ids:
            key = ("Student", sid, "STUDIED", "Concept", cid)
            rel = self._rels.get(key)
            if rel:
                scores.append(float(rel.get("mastery_score", 0.0)))
            else:
                scores.append(0.0)

        avg = sum(scores) / len(scores) if scores else 0.0
        return [{"avg_mastery": avg}]

    # -----------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------

    def reset(self) -> None:
        """Clear all data (useful between tests)."""
        for label in self._nodes:
            self._nodes[label].clear()
        self._rels.clear()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_graph_manager() -> MockGraphManager:
    """Provide a fresh MockGraphManager for each test."""
    gm = MockGraphManager()
    gm.connect()
    return gm


@pytest.fixture
def seeded_graph(mock_graph_manager: MockGraphManager) -> MockGraphManager:
    """
    A MockGraphManager pre-seeded with a small set of biology concepts
    and prerequisites for testing.
    """
    gm = mock_graph_manager
    from neurosync.knowledge.repositories.concepts import ConceptRepository
    from neurosync.knowledge.repositories.students import StudentRepository

    repo = ConceptRepository(gm)
    student_repo = StudentRepository(gm)

    # Seed concepts
    concepts = [
        ("bio_cells", "Cells", "prerequisite", 0.2, "biology"),
        ("bio_organelles", "Organelles", "prerequisite", 0.25, "biology"),
        ("bio_chloroplast", "Chloroplast", "prerequisite", 0.35, "biology"),
        ("bio_atp", "ATP", "prerequisite", 0.4, "biology"),
        ("bio_enzymes", "Enzymes", "prerequisite", 0.4, "biology"),
        ("bio_photosynthesis", "Photosynthesis", "core", 0.5, "biology"),
        ("bio_light_reactions", "Light Reactions", "core", 0.55, "biology"),
        ("bio_calvin_cycle", "Calvin Cycle", "core", 0.6, "biology"),
        ("bio_cellular_respiration", "Cellular Respiration", "core", 0.55, "biology"),
    ]
    for cid, name, category, diff, subject in concepts:
        repo.create_concept(cid, name, category, diff, subject=subject)

    # Seed prerequisites
    prereqs = [
        ("bio_organelles", "bio_cells"),
        ("bio_chloroplast", "bio_organelles"),
        ("bio_photosynthesis", "bio_chloroplast"),
        ("bio_photosynthesis", "bio_atp"),
        ("bio_photosynthesis", "bio_enzymes"),
        ("bio_light_reactions", "bio_photosynthesis"),
        ("bio_calvin_cycle", "bio_photosynthesis"),
        ("bio_calvin_cycle", "bio_light_reactions"),
        ("bio_cellular_respiration", "bio_atp"),
        ("bio_cellular_respiration", "bio_enzymes"),
    ]
    for cid, prereq_id in prereqs:
        repo.add_prerequisite(cid, prereq_id)

    # Next concepts
    repo.add_next_concept("bio_photosynthesis", "bio_light_reactions", 1)
    repo.add_next_concept("bio_photosynthesis", "bio_calvin_cycle", 2)

    # Create test student
    student_repo.create_student("arjun", name="Arjun")

    return gm
