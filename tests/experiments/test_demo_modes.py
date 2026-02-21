"""
Tests for demo modes — ScriptedDemo and LiveDemo.
"""

from __future__ import annotations

import pytest

from neurosync.experiments.demo_modes.scripted_demo import (
    DemoResult,
    DemoStep,
    ScriptedDemo,
)
from neurosync.experiments.demo_modes.live_demo import LiveDemo, LiveDemoResult
from neurosync.experiments.simulations.student_model import StudentProfile
from neurosync.core.constants import (
    MOMENT_ATTENTION_DROP,
    MOMENT_COGNITIVE_OVERLOAD,
    MOMENT_FRUSTRATION,
)


class TestScriptedDemo:
    """Tests for the ScriptedDemo class."""

    def test_script_has_17_steps(self):
        """The SCRIPT list has exactly 17 demo steps."""
        assert len(ScriptedDemo.SCRIPT) == 17

    def test_script_step_structure(self):
        """Each step in SCRIPT is a valid DemoStep."""
        for step in ScriptedDemo.SCRIPT:
            assert isinstance(step, DemoStep)
            assert isinstance(step.time_offset, (int, float))
            assert isinstance(step.action, str)
            assert step.time_offset >= 0

    def test_script_covers_5_minutes(self):
        """Script spans 300 seconds (5 minutes)."""
        last_offset = ScriptedDemo.SCRIPT[-1].time_offset
        assert last_offset == 300

    def test_script_contains_three_moments(self):
        """Script triggers M01, M02, and M07."""
        moments = [s.moment for s in ScriptedDemo.SCRIPT if s.moment]
        assert MOMENT_ATTENTION_DROP in moments
        assert MOMENT_COGNITIVE_OVERLOAD in moments
        assert MOMENT_FRUSTRATION in moments

    @pytest.mark.asyncio
    async def test_scripted_demo_run_returns_result(self):
        """Running the scripted demo returns a DemoResult."""
        demo = ScriptedDemo(realtime=False)
        result = await demo.run()
        assert isinstance(result, DemoResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_scripted_demo_executes_all_steps(self):
        """All 17 steps are executed."""
        demo = ScriptedDemo(realtime=False)
        result = await demo.run()
        assert result.steps_executed == 17

    @pytest.mark.asyncio
    async def test_scripted_demo_demonstrates_three_moments(self):
        """The demo hits M01, M02, and M07."""
        demo = ScriptedDemo(realtime=False)
        result = await demo.run()
        assert len(result.moments_demonstrated) == 3
        assert MOMENT_ATTENTION_DROP in result.moments_demonstrated
        assert MOMENT_COGNITIVE_OVERLOAD in result.moments_demonstrated
        assert MOMENT_FRUSTRATION in result.moments_demonstrated


class TestLiveDemo:
    """Tests for the LiveDemo class."""

    def test_live_demo_default_config(self):
        """LiveDemo has sensible defaults."""
        demo = LiveDemo()
        assert demo.duration_minutes == 5
        assert demo.cycle_interval == 0.25
        assert demo.realtime is False

    def test_live_demo_custom_profile(self):
        """LiveDemo accepts a custom StudentProfile."""
        profile = StudentProfile(student_id="custom", seed=99)
        demo = LiveDemo(profile=profile)
        assert demo.profile.student_id == "custom"
        assert demo.student.profile.seed == 99

    @pytest.mark.asyncio
    async def test_live_demo_short_run(self):
        """A short live demo completes and returns LiveDemoResult."""
        profile = StudentProfile(student_id="test_live", seed=1)
        demo = LiveDemo(
            duration_minutes=1,
            cycle_interval_ms=1000,  # 1-second cycles for speed
            realtime=False,
            profile=profile,
        )
        result = await demo.run()
        assert isinstance(result, LiveDemoResult)
        assert result.cycles_run > 0
        assert result.session_id.startswith("live_demo_")
        assert result.duration_seconds >= 0
