"""
Tests for GapDetector (M03) using MockGraphManager.
"""

import pytest

from neurosync.knowledge.detectors.gap_detector import GapDetector, GapResult


class TestGapDetector:
    """Test knowledge gap detection."""

    def test_no_gap_when_all_prereqs_strong(self, seeded_graph):
        """No gap detected when all prerequisites are well mastered."""
        detector = GapDetector(seeded_graph)
        prereq_data = [
            {"concept_id": "bio_chloroplast", "concept_name": "Chloroplast",
             "mastery_score": 0.8, "level": "proficient", "attempts": 5},
            {"concept_id": "bio_atp", "concept_name": "ATP",
             "mastery_score": 0.7, "level": "proficient", "attempts": 4},
        ]
        result = detector.detect("arjun", "bio_photosynthesis", prereq_data)
        assert result.gap_detected is False

    def test_gap_detected_weak_prereqs(self, seeded_graph):
        """Gap detected when prerequisites have low mastery."""
        detector = GapDetector(seeded_graph)
        prereq_data = [
            {"concept_id": "bio_chloroplast", "concept_name": "Chloroplast",
             "mastery_score": 0.1, "level": "novice", "attempts": 1},
            {"concept_id": "bio_atp", "concept_name": "ATP",
             "mastery_score": 0.2, "level": "novice", "attempts": 2},
            {"concept_id": "bio_enzymes", "concept_name": "Enzymes",
             "mastery_score": 0.7, "level": "proficient", "attempts": 5},
        ]
        result = detector.detect("arjun", "bio_photosynthesis", prereq_data)
        assert result.gap_detected is True
        assert len(result.weak_prerequisites) == 2
        assert result.strongest_gap == "bio_chloroplast"  # lowest mastery
        assert result.gap_severity > 0
        assert result.confidence > 0

    def test_gap_no_prereqs(self, seeded_graph):
        """No gap when there are no prerequisites."""
        detector = GapDetector(seeded_graph)
        result = detector.detect("arjun", "bio_cells", [])
        assert result.gap_detected is False

    def test_failure_streak_increases_confidence(self, seeded_graph):
        """Consecutive failures boost gap detection confidence."""
        detector = GapDetector(seeded_graph)
        # Record 3 consecutive failures
        for _ in range(3):
            detector.record_attempt("bio_photosynthesis", correct=False)

        prereq_data = [
            {"concept_id": "bio_chloroplast", "concept_name": "Chloroplast",
             "mastery_score": 0.2, "level": "novice", "attempts": 1},
        ]
        result = detector.detect("arjun", "bio_photosynthesis", prereq_data)
        assert result.gap_detected is True
        assert result.confidence > 0.6  # boosted by streak
