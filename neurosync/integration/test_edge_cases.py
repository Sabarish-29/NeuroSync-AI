"""
Integration tests — edge cases and stress tests.

Ensures the system handles unexpected inputs, boundary conditions,
and error states gracefully.
"""

from __future__ import annotations

import pytest

from neurosync.fusion.orchestrator import NeuroSyncOrchestrator
from neurosync.fusion.state import BehavioralSignals, WebcamSignals


class TestEdgeCases:
    """Stress tests and error-condition handling."""

    @pytest.mark.asyncio
    async def test_graph_unavailable_fallback(self):
        """System works when Neo4j graph is unreachable."""
        orch = NeuroSyncOrchestrator(
            session_id="no-graph",
            student_id="stu",
        )
        behavioral = BehavioralSignals()
        # Should not raise even if graph manager can't connect
        results = await orch.run_lesson_cycle(behavioral=behavioral)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_high_load_performance(self):
        """50 rapid cycles complete within reasonable time."""
        import time

        orch = NeuroSyncOrchestrator(session_id="perf", student_id="stu")
        behavioral = BehavioralSignals(
            frustration_score=0.3,
            fatigue_score=0.2,
        )

        start = time.time()
        for _ in range(50):
            await orch.run_lesson_cycle(behavioral=behavioral)
        elapsed = time.time() - start

        # 50 cycles should complete in well under 30 seconds
        assert elapsed < 30.0, f"50 cycles took {elapsed:.1f}s (too slow)"
