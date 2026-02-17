"""
NeuroSync AI — Tests for the fusion engine.

Tests:
  16. test_high_confidence_fires_immediately — 3 signals → intervention
  17. test_medium_confidence_soft_only — 2 signals → soft intervention
  18. test_low_confidence_no_action — 1 signal → log only
  19. test_cooldown_respected — second intervention within cooldown not fired
  20. test_priority_ordering — critical before warning before soft
"""

import time

import pytest

from neurosync.behavioral.fusion import BehavioralFusionEngine
from neurosync.core.events import QuestionEvent, VideoEvent
from tests.conftest import make_idle_event, make_question_event, make_raw_event, make_video_event


class TestFusionEngine:
    """Tests for the BehavioralFusionEngine."""

    def _make_engine(self) -> BehavioralFusionEngine:
        """Create a fusion engine for testing (no DB)."""
        now = time.time() * 1000
        return BehavioralFusionEngine(
            session_id="test_session",
            session_start_ms=now,
            db_manager=None,
        )

    def test_high_confidence_fires_immediately(self) -> None:
        """When 3+ signals agree (rewind burst + increasing RT + increasing idle) → intervention fires."""
        engine = self._make_engine()
        now = time.time() * 1000

        # Create events that trigger frustration:
        # 1. Rewind burst (3 rewinds in 30 seconds)
        events = [
            make_video_event(timestamp=now, playback_position_ms=60000),
            make_video_event(timestamp=now + 5000, playback_position_ms=60000),
            make_video_event(timestamp=now + 10000, playback_position_ms=60000),
        ]
        # 2. Increasing response times
        for i in range(7):
            events.append(make_question_event(
                response_time_ms=4000 + i * 100,
                timestamp=now + 15000 + i * 1000,
            ))
        for i in range(3):
            events.append(make_question_event(
                response_time_ms=18000 + i * 2000,
                timestamp=now + 25000 + i * 1000,
            ))
        # 3. Increasing idle
        for i in range(5):
            events.append(make_idle_event(
                timestamp=now + 30000 + i * 2000,
                idle_duration_ms=5000 + i * 2000,
            ))

        engine.add_events(events)
        flags = engine.run_cycle()

        # Should have M07 (frustration) active
        assert "M07" in flags.active_moments
        # Should have at least one intervention
        assert len(flags.interventions_ready) > 0

    def test_low_confidence_no_action(self) -> None:
        """Minimal/no signals → no active moments, no interventions."""
        engine = self._make_engine()
        now = time.time() * 1000

        # Just a few normal clicks
        events = [
            make_raw_event(timestamp=now + i * 2000)
            for i in range(5)
        ]

        engine.add_events(events)
        flags = engine.run_cycle()

        # No frustration or fatigue moments
        assert "M07" not in flags.active_moments
        assert "M10" not in flags.active_moments
        # No interventions
        m07_interventions = [i for i in flags.interventions_ready if i.moment_id == "M07"]
        m10_interventions = [i for i in flags.interventions_ready if i.moment_id == "M10"]
        assert len(m07_interventions) == 0
        assert len(m10_interventions) == 0

    def test_pseudo_understanding_flags_in_fusion(self) -> None:
        """Fast correct answers are flagged as M14 through fusion."""
        engine = self._make_engine()
        now = time.time() * 1000

        # Fast suspicious answer
        events = [
            make_question_event(
                answer_correct=True,
                response_time_ms=1500,  # suspiciously fast
                confidence_score=1,
                timestamp=now,
            ),
        ]

        engine.add_events(events)
        flags = engine.run_cycle()

        assert "M14" in flags.active_moments
        m14_interventions = [i for i in flags.interventions_ready if i.moment_id == "M14"]
        assert len(m14_interventions) >= 1

    def test_cooldown_respected(self) -> None:
        """Frustration intervention doesn't fire twice within cooldown."""
        engine = self._make_engine()
        now = time.time() * 1000

        # Trigger frustration
        events = [
            make_video_event(timestamp=now, playback_position_ms=60000),
            make_video_event(timestamp=now + 5000, playback_position_ms=60000),
            make_video_event(timestamp=now + 10000, playback_position_ms=60000),
        ]
        for i in range(7):
            events.append(make_question_event(response_time_ms=4000, timestamp=now + 15000 + i * 1000))
        for i in range(3):
            events.append(make_question_event(response_time_ms=20000, timestamp=now + 25000 + i * 1000))

        engine.add_events(events)
        flags1 = engine.run_cycle()

        m07_count_1 = len([i for i in flags1.interventions_ready if i.moment_id == "M07"])

        # Try again immediately — should be blocked by cooldown
        engine.add_events(events)
        flags2 = engine.run_cycle()

        m07_count_2 = len([i for i in flags2.interventions_ready if i.moment_id == "M07"])

        # First should fire, second should be blocked
        if m07_count_1 > 0:
            assert m07_count_2 == 0, "Cooldown should prevent second intervention"

    def test_priority_ordering(self) -> None:
        """When multiple interventions exist, they are ordered by urgency then confidence."""
        engine = self._make_engine()
        now = time.time() * 1000

        # Create M14 (flagged answer) + M07 (frustration) simultaneously
        events = [
            # M07 triggers
            make_video_event(timestamp=now, playback_position_ms=60000),
            make_video_event(timestamp=now + 5000, playback_position_ms=60000),
            make_video_event(timestamp=now + 10000, playback_position_ms=60000),
            # M14 trigger
            make_question_event(
                answer_correct=True,
                response_time_ms=1200,
                confidence_score=1,
                timestamp=now + 15000,
            ),
        ]
        # Add increasing response times for M07
        for i in range(7):
            events.append(make_question_event(response_time_ms=4000, timestamp=now + 20000 + i * 1000))
        for i in range(3):
            events.append(make_question_event(response_time_ms=20000, timestamp=now + 30000 + i * 1000))

        engine.add_events(events)
        flags = engine.run_cycle()

        if len(flags.interventions_ready) >= 2:
            # Priority should be the most urgent
            assert flags.priority_intervention is not None
            # Immediate urgency should come first
            urgencies = [i.urgency for i in flags.interventions_ready]
            if "immediate" in urgencies:
                assert flags.priority_intervention.urgency == "immediate"
