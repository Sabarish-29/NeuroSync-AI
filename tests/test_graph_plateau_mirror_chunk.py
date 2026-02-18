"""
Tests for PlateauDetector (M22), ConfidenceCollapseMirror (M09),
and ChunkTracker (M16).
"""

import time

import pytest

from neurosync.knowledge.detectors.plateau_detector import PlateauDetector, PlateauResult
from neurosync.knowledge.detectors.mirror import ConfidenceCollapseMirror, CollapseResult
from neurosync.knowledge.detectors.chunk_tracker import ChunkTracker, ChunkResult


class TestPlateauDetector:
    """Test mastery plateau detection."""

    def test_no_plateau_few_attempts(self, seeded_graph):
        """No plateau when attempts are below threshold."""
        detector = PlateauDetector(seeded_graph)
        result = detector.detect("arjun", "bio_cells", current_score=0.5, attempts=3)
        assert result.plateau_detected is False

    def test_plateau_detected(self, seeded_graph):
        """Plateau detected with enough attempts and low variance."""
        detector = PlateauDetector(seeded_graph)
        now = time.time()
        # Record consistent scores (low variance)
        for i in range(10):
            detector.record_score("arjun", "bio_cells", 0.50 + (i % 2) * 0.01,
                                  timestamp=now - 1200 + i * 60)

        result = detector.detect(
            student_id="arjun",
            concept_id="bio_cells",
            current_score=0.50,
            attempts=10,
            first_seen=now - 1200,  # 20 min ago
        )
        assert result.plateau_detected is True
        assert result.recommended_action == "try_alternative_explanation"
        assert result.confidence > 0.5

    def test_no_plateau_improving(self, seeded_graph):
        """No plateau when scores are improving (high variance)."""
        detector = PlateauDetector(seeded_graph)
        now = time.time()
        # Record improving scores with large steps (high variance > 0.05)
        for i in range(10):
            detector.record_score("arjun", "bio_cells", 0.05 + i * 0.10,
                                  timestamp=now - 1200 + i * 60)

        result = detector.detect(
            student_id="arjun",
            concept_id="bio_cells",
            current_score=0.95,
            attempts=10,
            first_seen=now - 1200,
        )
        assert result.plateau_detected is False


class TestConfidenceCollapseMirror:
    """Test confidence collapse detection."""

    def test_no_collapse_small_drop(self, seeded_graph):
        """No collapse when score drops less than threshold."""
        mirror = ConfidenceCollapseMirror(seeded_graph)
        result = mirror.detect("arjun", "bio_cells",
                               previous_score=0.70, current_score=0.60)
        assert result.collapse_detected is False

    def test_collapse_detected_large_drop(self, seeded_graph):
        """Collapse detected with drop exceeding threshold."""
        mirror = ConfidenceCollapseMirror(seeded_graph)
        # Record some history
        now = time.time()
        mirror.record_score("arjun", "bio_cells", 0.80, timestamp=now - 60)
        mirror.record_score("arjun", "bio_cells", 0.75, timestamp=now - 30)

        result = mirror.detect("arjun", "bio_cells",
                               previous_score=0.75, current_score=0.40)
        assert result.collapse_detected is True
        assert result.score_drop >= 0.25
        assert result.recommended_action in [
            "immediate_encouragement", "scaffold_review", "gentle_reassurance"
        ]
        assert result.confidence > 0.5

    def test_no_collapse_score_increase(self, seeded_graph):
        """No collapse when score increases."""
        mirror = ConfidenceCollapseMirror(seeded_graph)
        result = mirror.detect("arjun", "bio_cells",
                               previous_score=0.40, current_score=0.60)
        assert result.collapse_detected is False


class TestChunkTracker:
    """Test working memory overflow detection."""

    def test_no_overflow_few_concepts(self, seeded_graph):
        """No overflow with fewer than max new concepts."""
        tracker = ChunkTracker(seeded_graph)
        tracker.record_encounter("arjun", "bio_cells", mastery_score=0.1)
        tracker.record_encounter("arjun", "bio_organelles", mastery_score=0.0)

        result = tracker.detect("arjun")
        assert result.overflow_detected is False
        assert result.new_concepts_count == 2

    def test_overflow_too_many_new(self, seeded_graph):
        """Overflow detected when too many new concepts in window."""
        tracker = ChunkTracker(seeded_graph)
        now = time.time()
        for i, cid in enumerate([
            "bio_cells", "bio_organelles", "bio_chloroplast",
            "bio_atp", "bio_enzymes", "bio_photosynthesis",
        ]):
            tracker.record_encounter("arjun", cid, mastery_score=0.1,
                                     timestamp=now + i)

        result = tracker.detect("arjun")
        assert result.overflow_detected is True
        assert result.new_concepts_count == 6
        assert result.max_allowed == 4
        assert result.confidence > 0.5

    def test_no_overflow_high_mastery(self, seeded_graph):
        """High-mastery concepts don't count as new."""
        tracker = ChunkTracker(seeded_graph)
        # These have high mastery — should not be counted
        tracker.record_encounter("arjun", "bio_cells", mastery_score=0.8)
        tracker.record_encounter("arjun", "bio_organelles", mastery_score=0.9)
        tracker.record_encounter("arjun", "bio_chloroplast", mastery_score=0.7)
        tracker.record_encounter("arjun", "bio_atp", mastery_score=0.6)
        tracker.record_encounter("arjun", "bio_enzymes", mastery_score=0.5)

        result = tracker.detect("arjun")
        assert result.overflow_detected is False
        assert result.new_concepts_count == 0
