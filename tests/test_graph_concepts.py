"""
Tests for ConceptRepository using MockGraphManager.
"""

import pytest

from neurosync.knowledge.repositories.concepts import ConceptRepository


class TestConceptRepository:
    """Test concept CRUD operations with MockGraphManager."""

    def test_create_and_get_concept(self, mock_graph_manager):
        """Create a concept and retrieve it."""
        repo = ConceptRepository(mock_graph_manager)
        success = repo.create_concept(
            concept_id="test_concept",
            name="Test Concept",
            category="core",
            difficulty=0.5,
            description="A test concept",
            subject="test",
        )
        assert success is True

        concept = repo.get_concept("test_concept")
        assert concept is not None
        assert concept["concept_id"] == "test_concept"
        assert concept["name"] == "Test Concept"
        assert concept["category"] == "core"
        assert concept["difficulty"] == 0.5

    def test_get_all_concepts(self, seeded_graph):
        """Get all seeded concepts."""
        repo = ConceptRepository(seeded_graph)
        concepts = repo.get_all_concepts()
        assert len(concepts) >= 9  # seeded_graph has 9 concepts

    def test_get_concepts_by_subject(self, seeded_graph):
        """Filter concepts by subject."""
        repo = ConceptRepository(seeded_graph)
        bio = repo.get_all_concepts(subject="biology")
        assert len(bio) >= 9
        assert all(c["subject"] == "biology" for c in bio)

    def test_add_and_get_prerequisites(self, seeded_graph):
        """Verify prerequisite relationships."""
        repo = ConceptRepository(seeded_graph)
        prereqs = repo.get_prerequisites("bio_photosynthesis")
        prereq_ids = [p["concept_id"] for p in prereqs]
        assert "bio_chloroplast" in prereq_ids
        assert "bio_atp" in prereq_ids
        assert "bio_enzymes" in prereq_ids

    def test_get_dependents(self, seeded_graph):
        """Get concepts that depend on a prerequisite."""
        repo = ConceptRepository(seeded_graph)
        dependents = repo.get_dependents("bio_atp")
        dep_ids = [d["concept_id"] for d in dependents]
        assert "bio_photosynthesis" in dep_ids

    def test_next_concepts(self, seeded_graph):
        """Get next concepts in learning path."""
        repo = ConceptRepository(seeded_graph)
        next_c = repo.get_next_concepts("bio_photosynthesis")
        assert len(next_c) == 2
        next_ids = [n["concept_id"] for n in next_c]
        assert "bio_light_reactions" in next_ids
        assert "bio_calvin_cycle" in next_ids
