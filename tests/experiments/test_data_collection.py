"""
Tests for data collection — SessionRecorder, MomentTracker, EventExporter.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from neurosync.core.constants import ALL_MOMENTS
from neurosync.experiments.data_collection.session_recorder import SessionRecorder
from neurosync.experiments.data_collection.moment_tracker import MomentTracker
from neurosync.experiments.data_collection.event_exporter import EventExporter
from neurosync.experiments.framework import ExperimentResult


class TestDataCollection:
    """Tests for data collection components."""

    def test_session_recorder_lifecycle(self, tmp_path):
        """SessionRecorder start → record → end works correctly."""
        rec = SessionRecorder(output_dir=str(tmp_path / "sessions"))
        rec.start_session("sess-1", metadata={"experiment": "E1"})

        assert "sess-1" in rec.active_session_ids

        rec.record_event("sess-1", {"type": "quiz_answer", "correct": True})
        rec.record_signal("sess-1", {"attention": 0.85})
        rec.record_intervention("sess-1", {"moment_id": "M01"})

        rec.end_session("sess-1")

        data = rec.get_session_data("sess-1")
        assert data is not None
        assert len(data["events"]) == 1
        assert len(data["signals"]) == 1
        assert len(data["interventions"]) == 1
        assert "ended_at" in data

    def test_session_recorder_export_json(self, tmp_path):
        """export_session writes a valid JSON file."""
        rec = SessionRecorder(output_dir=str(tmp_path / "exports"))
        rec.start_session("sess-2")
        rec.record_event("sess-2", {"type": "test"})
        rec.end_session("sess-2")

        path = rec.export_session("sess-2")
        assert Path(path).exists()

        with open(path) as f:
            data = json.load(f)
        assert data["session_id"] == "sess-2"
        assert len(data["events"]) == 1

    def test_session_recorder_multiple_sessions(self, tmp_path):
        """Two sessions recorded independently without cross-talk."""
        rec = SessionRecorder(output_dir=str(tmp_path / "multi"))
        rec.start_session("A")
        rec.start_session("B")

        rec.record_event("A", {"val": 1})
        rec.record_event("A", {"val": 2})
        rec.record_event("B", {"val": 100})

        assert len(rec.get_session_data("A")["events"]) == 2
        assert len(rec.get_session_data("B")["events"]) == 1

    def test_moment_tracker_counts(self):
        """MomentTracker counts moments correctly with zero-fill."""
        tracker = MomentTracker()
        tracker.record_moment("s1", "M01", timestamp=1.0)
        tracker.record_moment("s1", "M01", timestamp=2.0)
        tracker.record_moment("s1", "M07", timestamp=3.0)

        counts = tracker.get_moment_counts("s1")
        assert counts["M01"] == 2
        assert counts["M07"] == 1
        # Unfired moments should be zero
        assert counts.get("M22", 0) == 0
        # All 22 moments should appear in counts
        assert len(counts) >= len(ALL_MOMENTS)

    def test_moment_tracker_coverage(self):
        """Coverage = fraction of 22 moments that fired at least once."""
        tracker = MomentTracker()
        tracker.record_moment("s1", "M01", timestamp=1.0)
        tracker.record_moment("s1", "M02", timestamp=2.0)

        coverage = tracker.get_coverage("s1")
        expected = 2 / len(ALL_MOMENTS)
        assert abs(coverage - expected) < 0.001

    def test_moment_tracker_timeline(self):
        """Timeline returns events sorted by timestamp."""
        tracker = MomentTracker()
        tracker.record_moment("s1", "M03", timestamp=5.0)
        tracker.record_moment("s1", "M01", timestamp=1.0)
        tracker.record_moment("s1", "M02", timestamp=3.0)

        timeline = tracker.get_moment_timeline("s1")
        timestamps = [e.timestamp for e in timeline]
        assert timestamps == sorted(timestamps)
        assert timeline[0].moment_id == "M01"

    def test_event_exporter_csv(self, tmp_path):
        """EventExporter writes valid CSV with correct rows."""
        exporter = EventExporter(output_dir=str(tmp_path / "csv_out"))
        results = [
            ExperimentResult(
                experiment_id="E1",
                participant_id=f"P{i}",
                condition="control" if i % 2 == 0 else "treatment",
                session_id=f"s{i}",
                quiz_score=0.7 + i * 0.01,
                completion_rate=0.9,
            )
            for i in range(4)
        ]

        path = exporter.export_results_csv(results, filename="test.csv")
        assert Path(path).exists()

        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 4
        assert rows[0]["participant_id"] == "P0"
        assert rows[0]["experiment_id"] == "E1"
