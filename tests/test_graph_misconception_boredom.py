"""
Tests for MisconceptionDetector (M15) and MasteryChecker (M06).
"""

import pytest

from neurosync.knowledge.detectors.misconception_detector import MisconceptionDetector, MisconceptionResult
from neurosync.knowledge.detectors.mastery_checker import MasteryChecker, BoredomResult
from neurosync.knowledge.repositories.misconceptions import MisconceptionRepository


class TestMisconceptionDetector:
    """Test misconception detection."""

    def test_no_misconception_correct_answer(self, seeded_graph):
        """No misconception when there's no wrong answer."""
        detector = MisconceptionDetector(seeded_graph)
        result = detector.detect(
            student_id="arjun",
            concept_id="bio_photosynthesis",
            wrong_answer="",
            known_misconceptions=[],
        )
        assert result.misconception_detected is False

    def test_misconception_matched(self, seeded_graph):
        """Misconception detected when wrong answer matches known pattern."""
        # Seed a misconception
        mc_repo = MisconceptionRepository(seeded_graph)
        mc_repo.create_misconception(
            misconception_id="mc_photo_food",
            concept_id="bio_photosynthesis",
            description="Plants eat food from the soil",
            common_wrong_answer="soil nutrients",
            correction="Plants make their own food via photosynthesis",
            severity=0.7,
        )

        detector = MisconceptionDetector(seeded_graph)
        known = mc_repo.get_misconceptions_for_concept("bio_photosynthesis")

        result = detector.detect(
            student_id="arjun",
            concept_id="bio_photosynthesis",
            wrong_answer="soil nutrients",
            student_confidence=4,
            known_misconceptions=known,
        )
        assert result.misconception_detected is True
        assert result.misconception_id == "mc_photo_food"
        assert result.correction != ""
        assert result.severity == 0.7

    def test_repeat_wrong_answer_escalates(self, seeded_graph):
        """Repeated wrong answers increase confidence and change action."""
        detector = MisconceptionDetector(seeded_graph)
        mc_repo = MisconceptionRepository(seeded_graph)
        mc_repo.create_misconception(
            misconception_id="mc_photo_food",
            concept_id="bio_photosynthesis",
            description="Plants eat food from the soil",
            common_wrong_answer="soil nutrients",
            correction="Plants make food via photosynthesis",
            severity=0.7,
        )
        known = mc_repo.get_misconceptions_for_concept("bio_photosynthesis")

        # First wrong answer
        r1 = detector.detect("arjun", "bio_photosynthesis", "soil nutrients",
                             known_misconceptions=known)
        assert r1.repeat_count == 1
        assert r1.recommended_action == "gentle_hint"

        # Second wrong answer (same)
        r2 = detector.detect("arjun", "bio_photosynthesis", "soil nutrients",
                             student_confidence=4, known_misconceptions=known)
        assert r2.repeat_count == 2
        assert r2.confidence > r1.confidence

    def test_novel_misconception_flagged(self, seeded_graph):
        """Repeated unknown wrong answers flagged as novel misconception."""
        detector = MisconceptionDetector(seeded_graph)
        # Give same wrong answer 3 times (threshold is 2)
        for _ in range(2):
            detector.detect("arjun", "bio_cells", "mitochondria is the brain")

        result = detector.detect("arjun", "bio_cells", "mitochondria is the brain")
        assert result.misconception_detected is True
        assert result.recommended_action == "investigate_novel_misconception"


class TestMasteryChecker:
    """Test stealth boredom / mastery checker."""

    def test_no_boredom_low_mastery(self, seeded_graph):
        """No boredom when mastery is low."""
        checker = MasteryChecker(seeded_graph)
        result = checker.detect("arjun", "bio_photosynthesis", mastery_score=0.3)
        assert result.boredom_detected is False

    def test_boredom_high_mastery_many_repeats(self, seeded_graph):
        """Boredom detected with high mastery and many encounters."""
        checker = MasteryChecker(seeded_graph)
        # Record 6 encounters (threshold is 5)
        for _ in range(6):
            checker.record_encounter("arjun", "bio_cells")

        result = checker.detect(
            student_id="arjun",
            concept_id="bio_cells",
            mastery_score=0.95,
            next_concepts=[
                {"concept_id": "bio_organelles", "name": "Organelles"},
            ],
        )
        assert result.boredom_detected is True
        assert result.recommended_action == "advance_to_next"
        assert "bio_organelles" in result.recommended_next_concepts

    def test_no_boredom_few_repeats(self, seeded_graph):
        """No boredom if mastery is high but not enough repeats."""
        checker = MasteryChecker(seeded_graph)
        checker.record_encounter("arjun", "bio_atp")
        checker.record_encounter("arjun", "bio_atp")

        result = checker.detect("arjun", "bio_atp", mastery_score=0.95)
        assert result.boredom_detected is False
