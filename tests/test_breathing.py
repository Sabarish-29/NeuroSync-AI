"""Tests for the breathing exercise intervention (Step 9)."""

from neurosync.readiness.interventions.breathing import (
    BreathPhase,
    phase_at,
    total_duration_seconds,
    CYCLE_DURATION,
    CYCLES,
)


class TestBreathing:
    """Breathing exercise tests."""

    def test_total_duration(self) -> None:
        """Total duration should be (4+4+6)*8 = 112 seconds."""
        assert total_duration_seconds() == 112.0

    def test_phase_mid_cycle(self) -> None:
        """At 5 seconds into the first cycle we should be in the HOLD phase."""
        # 0-4 = inhale, 4-8 = hold
        state = phase_at(5.0)
        assert state.phase == BreathPhase.HOLD
        assert state.current_cycle == 1
        assert state.is_complete is False

    def test_complete_after_all_cycles(self) -> None:
        """After 112+ seconds the exercise should be COMPLETE."""
        state = phase_at(120.0)
        assert state.phase == BreathPhase.COMPLETE
        assert state.is_complete is True
        assert state.current_cycle == CYCLES
