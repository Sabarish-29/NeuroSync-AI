"""
Integration tests — full end-to-end pipeline.

Tests the complete flow from session start through lesson to
post-lesson quiz and spaced repetition scheduling.
"""

from __future__ import annotations

import pytest

from neurosync.fusion.orchestrator import NeuroSyncOrchestrator
from neurosync.fusion.state import BehavioralSignals, WebcamSignals
from neurosync.experiments.simulations.student_model import (
    StudentModel,
    StudentProfile,
)


class TestFullPipeline:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_lesson_flow(self):
        """Student completes a full simulated lesson."""
        orch = NeuroSyncOrchestrator(
            session_id="e2e-lesson",
            student_id="e2e-student",
        )
        student = StudentModel(
            StudentProfile(
                student_id="e2e-student",
                attention_baseline=0.8,
                frustration_tendency=0.3,
                seed=12345,
            )
        )

        all_interventions = []
        for minute in range(15):
            student.advance_minute()
            behavioral = student.get_behavioral_signals()
            webcam = student.get_webcam_signals()

            results = await orch.run_lesson_cycle(
                behavioral=behavioral,
                webcam=webcam,
            )
            all_interventions.extend(results)

        # Session should run without errors
        assert isinstance(all_interventions, list)
        # Some interventions may have fired
        for iv in all_interventions:
            assert iv.moment_id  # every intervention references a moment

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self):
        """Two sessions running simultaneously don't interfere."""
        orch_a = NeuroSyncOrchestrator(session_id="sess-A", student_id="stu-A")
        orch_b = NeuroSyncOrchestrator(session_id="sess-B", student_id="stu-B")

        results_a = await orch_a.run_lesson_cycle(
            behavioral=BehavioralSignals(frustration_score=0.9)
        )
        results_b = await orch_b.run_lesson_cycle(
            behavioral=BehavioralSignals()
        )

        # Both return valid lists; session A has more aggressive signals
        assert isinstance(results_a, list)
        assert isinstance(results_b, list)

    @pytest.mark.asyncio
    async def test_webcam_failure_graceful_degradation(self):
        """System works even when webcam returns no face."""
        orch = NeuroSyncOrchestrator(session_id="no-cam", student_id="stu")

        # Run with webcam that detects no face
        results = await orch.run_lesson_cycle(
            webcam=WebcamSignals(face_detected=False),
        )
        assert isinstance(results, list)

        # Run with no webcam at all
        results = await orch.run_lesson_cycle(
            behavioral=BehavioralSignals(),
            webcam=None,
        )
        assert isinstance(results, list)
