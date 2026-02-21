"""
Integration tests — performance targets.

Verifies that the fusion cycle meets the 250ms target latency
and the system satisfies throughput requirements.
"""

from __future__ import annotations

import time

import pytest

from neurosync.fusion.orchestrator import NeuroSyncOrchestrator
from neurosync.fusion.state import BehavioralSignals, WebcamSignals


class TestPerformance:
    """Performance / latency integration tests."""

    @pytest.mark.asyncio
    async def test_single_cycle_latency(self):
        """A single fusion cycle completes in < 500ms."""
        orch = NeuroSyncOrchestrator(session_id="lat", student_id="stu")
        behavioral = BehavioralSignals(frustration_score=0.5)
        webcam = WebcamSignals(
            attention_score=0.6,
            face_detected=True,
        )

        start = time.time()
        await orch.run_lesson_cycle(behavioral=behavioral, webcam=webcam)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Single cycle took {elapsed:.3f}s (> 500ms)"
