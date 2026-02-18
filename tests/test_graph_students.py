"""
Tests for StudentRepository using MockGraphManager.
"""

import pytest

from neurosync.knowledge.repositories.students import StudentRepository
from neurosync.knowledge.repositories.concepts import ConceptRepository


class TestStudentRepository:
    """Test student CRUD and relationship operations."""

    def test_create_and_get_student(self, mock_graph_manager):
        """Create a student and retrieve them."""
        repo = StudentRepository(mock_graph_manager)
        success = repo.create_student("student_1", name="Alice")
        assert success is True

        student = repo.get_student("student_1")
        assert student is not None
        assert student["student_id"] == "student_1"
        assert student["name"] == "Alice"

    def test_record_study_correct(self, seeded_graph):
        """Record a correct study attempt."""
        repo = StudentRepository(seeded_graph)
        success = repo.record_study("arjun", "bio_photosynthesis", correct=True)
        assert success is True

        mastery = repo.get_mastery("arjun", "bio_photosynthesis")
        assert mastery is not None
        assert mastery["attempts"] == 1
        assert mastery["correct"] == 1
        assert mastery["streak"] == 1

    def test_record_study_incorrect(self, seeded_graph):
        """Record an incorrect study attempt."""
        repo = StudentRepository(seeded_graph)
        repo.record_study("arjun", "bio_photosynthesis", correct=False)

        mastery = repo.get_mastery("arjun", "bio_photosynthesis")
        assert mastery is not None
        assert mastery["incorrect"] == 1
        assert mastery["streak"] == 0

    def test_multiple_attempts_tracking(self, seeded_graph):
        """Multiple attempts update running stats correctly."""
        repo = StudentRepository(seeded_graph)
        repo.record_study("arjun", "bio_cells", correct=True)
        repo.record_study("arjun", "bio_cells", correct=True)
        repo.record_study("arjun", "bio_cells", correct=False)

        mastery = repo.get_mastery("arjun", "bio_cells")
        assert mastery["attempts"] == 3
        assert mastery["correct"] == 2
        assert mastery["incorrect"] == 1
        assert mastery["streak"] == 0  # reset by incorrect

    def test_mark_struggle(self, seeded_graph):
        """Mark a concept as struggling."""
        repo = StudentRepository(seeded_graph)
        repo.mark_struggle("arjun", "bio_calvin_cycle")
        repo.mark_struggle("arjun", "bio_calvin_cycle")

        struggles = repo.get_struggles("arjun")
        assert len(struggles) == 1
        assert struggles[0]["concept_id"] == "bio_calvin_cycle"
        assert struggles[0]["failure_count"] == 2
