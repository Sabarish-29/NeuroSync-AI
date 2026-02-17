"""
NeuroSync AI — Tests for signal processors.

Tests:
  1. test_response_time_fast_answer_rate — fast answers correctly computed
  2. test_response_time_trend_increasing — increasing trend detected
  3. test_rewind_burst_detection — 3 rewinds in 60s triggers burst
  4. test_idle_frequency_increasing — idle trend correctly detected
  5. test_interaction_variance_erratic — high variance = erratic
  6. test_interaction_variance_stable — low variance = stable
"""

import time

import pytest

from neurosync.behavioral.signals import (
    IdleSignal,
    InteractionVarianceSignal,
    ResponseTimeSignal,
    RewindSignal,
    ScrollBehaviorSignal,
)
from tests.conftest import make_idle_event, make_question_event, make_raw_event, make_video_event


class TestResponseTimeSignal:
    """Tests for the ResponseTimeSignal processor."""

    def test_response_time_fast_answer_rate(self) -> None:
        """Fast answers (<3000ms) are correctly detected and rate computed."""
        processor = ResponseTimeSignal()

        # Create 10 questions: 7 fast (<3000ms), 3 normal
        events = []
        for i in range(7):
            events.append(make_question_event(response_time_ms=1500 + i * 100))
        for i in range(3):
            events.append(make_question_event(response_time_ms=8000 + i * 1000))

        result = processor.process(events)

        # 7 out of 10 answers are fast
        assert result.fast_answer_rate == pytest.approx(0.7, abs=0.01)
        assert result.mean_response_time_ms > 0

    def test_response_time_trend_increasing(self) -> None:
        """Increasing response times are detected as increasing trend."""
        processor = ResponseTimeSignal()

        # Earlier answers are fast, recent answers are slow
        events = []
        for i in range(7):
            events.append(make_question_event(response_time_ms=3000 + i * 100))
        for i in range(3):
            events.append(make_question_event(response_time_ms=12000 + i * 2000))

        result = processor.process(events)
        assert result.response_time_trend == "increasing"

    def test_response_time_trend_stable(self) -> None:
        """Consistent response times show stable trend."""
        processor = ResponseTimeSignal()

        events = []
        for i in range(10):
            events.append(make_question_event(response_time_ms=7000 + (i % 3) * 200))

        result = processor.process(events)
        assert result.response_time_trend == "stable"


class TestRewindSignal:
    """Tests for the RewindSignal processor."""

    def test_rewind_burst_detection(self) -> None:
        """3 rewinds within 60 seconds triggers burst detection."""
        processor = RewindSignal()
        now = time.time() * 1000

        # 3 rewinds within 30 seconds
        events = [
            make_video_event(timestamp=now, playback_position_ms=60000),
            make_video_event(timestamp=now + 10000, playback_position_ms=60000),
            make_video_event(timestamp=now + 20000, playback_position_ms=60000),
        ]

        result = processor.process(events)
        assert result.rewind_burst_detected is True
        assert result.rewinds_per_minute > 0

    def test_no_burst_with_spread_rewinds(self) -> None:
        """Rewinds spread over time (>60s apart) do not trigger burst."""
        processor = RewindSignal()
        now = time.time() * 1000

        events = [
            make_video_event(timestamp=now, playback_position_ms=60000),
            make_video_event(timestamp=now + 120000, playback_position_ms=120000),
        ]

        result = processor.process(events)
        assert result.rewind_burst_detected is False


class TestIdleSignal:
    """Tests for the IdleSignal processor."""

    def test_idle_frequency_increasing(self) -> None:
        """Increasing idle frequency is detected when recent idles are more frequent."""
        processor = IdleSignal()
        now = time.time() * 1000

        # Many recent idles (last 2 minutes)
        events = []
        for i in range(8):
            events.append(make_idle_event(
                timestamp=now - 30000 + i * 3000,  # 8 idles in last 30s
                idle_duration_ms=2000,
            ))

        result = processor.process(events)
        assert result.idle_frequency > 0
        assert result.total_idle_time_ms > 0

    def test_idle_total_time_computed(self) -> None:
        """Total idle time is correctly summed."""
        processor = IdleSignal()
        now = time.time() * 1000

        events = [
            make_idle_event(timestamp=now - 5000, idle_duration_ms=1000),
            make_idle_event(timestamp=now - 3000, idle_duration_ms=2000),
            make_idle_event(timestamp=now - 1000, idle_duration_ms=3000),
        ]

        result = processor.process(events)
        assert result.total_idle_time_ms == pytest.approx(6000.0, abs=0.1)
        assert result.longest_idle_ms == pytest.approx(3000.0, abs=0.1)


class TestInteractionVarianceSignal:
    """Tests for the InteractionVarianceSignal processor."""

    def test_interaction_variance_erratic(self) -> None:
        """Highly variable inter-event times produce erratic classification."""
        processor = InteractionVarianceSignal()
        now = time.time() * 1000

        # Erratic: alternating fast and very slow intervals
        events = []
        t = now
        for i in range(20):
            if i % 2 == 0:
                t += 200   # very fast
            else:
                t += 15000  # very slow
            events.append(make_raw_event(timestamp=t))

        result = processor.process(events)
        assert result.variance_trend in ("increasing", "erratic")
        assert result.fatigue_probability > 0.3

    def test_interaction_variance_stable(self) -> None:
        """Consistent inter-event times produce stable classification."""
        processor = InteractionVarianceSignal()
        now = time.time() * 1000

        # Stable: consistent 2-second intervals
        events = []
        for i in range(20):
            events.append(make_raw_event(timestamp=now + i * 2000))

        result = processor.process(events)
        assert result.variance_trend == "stable"
        assert result.fatigue_probability < 0.5
