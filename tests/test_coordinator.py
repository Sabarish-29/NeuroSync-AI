"""
Step 5 — FusionCoordinator tests (3 tests).
"""

from __future__ import annotations

import pytest

from neurosync.fusion.agents.attention_agent import AttentionAgent
from neurosync.fusion.agents.fatigue_agent import FatigueAgent
from neurosync.fusion.coordinator import FusionCoordinator
from neurosync.fusion.state import BehavioralSignals, WebcamSignals


class TestFusionCoordinator:

    @pytest.mark.asyncio
    async def test_full_cycle_completes(self):
        """process_cycle with live agents returns a list."""
        coord = FusionCoordinator([AttentionAgent(), FatigueAgent()])
        result = await coord.process_cycle(
            session_id="s1",
            student_id="stu1",
            behavioral=BehavioralSignals(fatigue_score=0.85),
        )
        assert isinstance(result, list)
        # Fatigue is critical → should fire force_break
        assert any(i.intervention_type == "force_break" for i in result)

    @pytest.mark.asyncio
    async def test_no_interventions_on_normal(self):
        """Normal state → empty list, no errors."""
        coord = FusionCoordinator([AttentionAgent(), FatigueAgent()])
        result = await coord.process_cycle(
            session_id="s1",
            student_id="stu1",
            behavioral=BehavioralSignals(),
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_cycles_increment(self):
        """Cycle count increments each call."""
        coord = FusionCoordinator([AttentionAgent()])
        await coord.process_cycle("s", "stu", BehavioralSignals())
        await coord.process_cycle("s", "stu", BehavioralSignals())
        await coord.process_cycle("s", "stu", BehavioralSignals())
        assert coord.cycle_count == 3
