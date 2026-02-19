"""
Step 5 — NeuroSyncOrchestrator tests (2 tests).
"""

from __future__ import annotations

import pytest

from neurosync.fusion.orchestrator import NeuroSyncOrchestrator
from neurosync.fusion.state import BehavioralSignals


class TestOrchestrator:

    def test_initialises_all_agents(self):
        """Orchestrator creates all 8 agents."""
        orch = NeuroSyncOrchestrator(session_id="s", student_id="stu")
        assert len(orch.agents) == 8

    @pytest.mark.asyncio
    async def test_run_lesson_cycle(self):
        """run_lesson_cycle returns list, no crashes."""
        orch = NeuroSyncOrchestrator()
        result = await orch.run_lesson_cycle(
            behavioral=BehavioralSignals(),
        )
        assert isinstance(result, list)
