"""
Tests for MasteryRepository using MockGraphManager.
"""

import pytest

from neurosync.knowledge.repositories.mastery import MasteryRepository, _score_to_level
from neurosync.knowledge.repositories.students import StudentRepository


class TestMasteryRepository:
    """Test mastery computation and tracking."""

    def test_score_to_level(self):
        """Score-to-level mapping works correctly."""
        assert _score_to_level(0.0) == "novice"
        assert _score_to_level(0.29) == "novice"
        assert _score_to_level(0.30) == "developing"
        assert _score_to_level(0.59) == "developing"
        assert _score_to_level(0.60) == "proficient"
        assert _score_to_level(0.84) == "proficient"
        assert _score_to_level(0.85) == "mastered"
        assert _score_to_level(1.0) == "mastered"

    def test_compute_mastery_correct_answer(self, seeded_graph):
        """Correct answer increases mastery score."""
        student_repo = StudentRepository(seeded_graph)
        student_repo.record_study("arjun", "bio_cells", correct=True)

        mastery_repo = MasteryRepository(seeded_graph)
        result = mastery_repo.compute_mastery_score(
            student_id="arjun",
            concept_id="bio_cells",
            correct=True,
            response_time_ms=3000.0,
        )
        assert result["new_score"] > result["previous_score"]
        assert result["score_delta"] > 0

    def test_compute_mastery_incorrect_answer(self, seeded_graph):
        """Incorrect answer decreases mastery score."""
        student_repo = StudentRepository(seeded_graph)
        # Build up some mastery first
        student_repo.record_study("arjun", "bio_cells", correct=True)
        mastery_repo = MasteryRepository(seeded_graph)
        mastery_repo.compute_mastery_score("arjun", "bio_cells", correct=True)
        mastery_repo.compute_mastery_score("arjun", "bio_cells", correct=True)

        # Now get wrong
        result = mastery_repo.compute_mastery_score("arjun", "bio_cells", correct=False)
        assert result["score_delta"] < 0

    def test_prerequisite_mastery(self, seeded_graph):
        """Get prerequisite mastery for gap detection."""
        student_repo = StudentRepository(seeded_graph)
        # Study some prerequisites
        student_repo.record_study("arjun", "bio_chloroplast", correct=True)
        student_repo.record_study("arjun", "bio_atp", correct=True)

        mastery_repo = MasteryRepository(seeded_graph)
        prereqs = mastery_repo.get_prerequisite_mastery("arjun", "bio_photosynthesis")
        assert len(prereqs) == 3  # chloroplast, atp, enzymes
        prereq_ids = [p["concept_id"] for p in prereqs]
        assert "bio_chloroplast" in prereq_ids
        assert "bio_atp" in prereq_ids
        assert "bio_enzymes" in prereq_ids
