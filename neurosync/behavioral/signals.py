"""
NeuroSync AI — Behavioral signal processors.

Each processor uses a rolling window (deque) over recent events to compute
signal values. All processors follow the SignalProcessor protocol so that
Steps 2 and 10 can inject webcam/EEG processors without rewriting fusion.

Protocol:
    process(events) -> SignalResult
    get_current_value() -> dict[str, float]
    reset() -> None
"""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Any, Protocol, runtime_checkable

import numpy as np
from loguru import logger
from scipy import stats as scipy_stats

from neurosync.config.settings import get_threshold
from neurosync.core.constants import (
    SCROLL_ENGAGED,
    SCROLL_RUSHING,
    SCROLL_SKIMMING,
    TREND_DECREASING,
    TREND_INCREASING,
    TREND_STABLE,
)
from neurosync.core.events import (
    IdleEvent,
    IdleResult,
    InteractionVarianceResult,
    QuestionEvent,
    RawEvent,
    ResponseTimeResult,
    RewindResult,
    ScrollResult,
    SessionPacingResult,
    SignalResult,
    VideoEvent,
)


# =============================================================================
# Protocol for signal processors (extensibility point)
# =============================================================================

@runtime_checkable
class SignalProcessor(Protocol):
    """Interface that all signal processors must follow."""

    def process(self, events: list[RawEvent]) -> SignalResult:
        """Process a batch of events and return computed signal."""
        ...

    def get_current_value(self) -> dict[str, float]:
        """Return current signal values as a flat dict."""
        ...

    def reset(self) -> None:
        """Reset internal state."""
        ...


# =============================================================================
# ResponseTimeSignal
# =============================================================================

class ResponseTimeSignal:
    """
    Tracks question response times to detect patterns.

    Window: Last N questions (configurable, default 10).
    Outputs: mean response time, trend, fast answer rate.
    """

    def __init__(self) -> None:
        self._window_size = int(get_threshold("RESPONSE_TIME_WINDOW"))
        self._fast_threshold = get_threshold("FAST_ANSWER_THRESHOLD_MS")
        self._times: deque[float] = deque(maxlen=self._window_size)
        self._result = ResponseTimeResult()

    def process(self, events: list[RawEvent]) -> ResponseTimeResult:
        """Process question events and update response time metrics."""
        for event in events:
            if isinstance(event, QuestionEvent) and event.response_time_ms is not None:
                self._times.append(event.response_time_ms)

        if len(self._times) == 0:
            self._result = ResponseTimeResult()
            return self._result

        times_list = list(self._times)
        mean_rt = float(np.mean(times_list))
        fast_count = sum(1 for t in times_list if t < self._fast_threshold)
        fast_rate = fast_count / len(times_list)

        # Trend: compare mean of last 3 vs mean of previous 7 (or whatever we have)
        trend = TREND_STABLE
        if len(times_list) >= 4:
            split = max(1, len(times_list) - 3)
            recent_mean = float(np.mean(times_list[split:]))
            earlier_mean = float(np.mean(times_list[:split]))
            if earlier_mean > 0:
                ratio = recent_mean / earlier_mean
                if ratio > 1.2:
                    trend = TREND_INCREASING
                elif ratio < 0.8:
                    trend = TREND_DECREASING

        self._result = ResponseTimeResult(
            mean_response_time_ms=round(mean_rt, 1),
            response_time_trend=trend,
            fast_answer_rate=round(fast_rate, 3),
        )
        logger.debug("ResponseTime: mean={}ms, trend={}, fast_rate={}", mean_rt, trend, fast_rate)
        return self._result

    def get_current_value(self) -> dict[str, float]:
        return {
            "response_time_mean_ms": self._result.mean_response_time_ms,
            "fast_answer_rate": self._result.fast_answer_rate,
        }

    def reset(self) -> None:
        self._times.clear()
        self._result = ResponseTimeResult()


# =============================================================================
# RewindSignal
# =============================================================================

class RewindSignal:
    """
    Tracks video rewind frequency as confusion/frustration signal.

    Window: Last 5 minutes of video events.
    """

    def __init__(self) -> None:
        self._window_minutes = get_threshold("REWIND_WINDOW_MINUTES")
        self._burst_threshold = int(get_threshold("REWIND_BURST_THRESHOLD"))
        self._burst_window_seconds = get_threshold("REWIND_BURST_WINDOW_SECONDS")
        self._rewind_events: deque[float] = deque()  # timestamps of rewinds
        self._segment_rewinds: dict[str, int] = {}  # segment_id -> count
        self._result = RewindResult()

    def process(self, events: list[RawEvent]) -> RewindResult:
        """Process video events and detect rewind patterns."""
        now = time.time() * 1000.0

        for event in events:
            if isinstance(event, VideoEvent) and event.event_type == "video_rewind":
                self._rewind_events.append(event.timestamp)
                # Track segment (30-second chunk)
                segment_id = str(int(event.playback_position_ms / 30000))
                self._segment_rewinds[segment_id] = self._segment_rewinds.get(segment_id, 0) + 1

        # Prune old events outside window
        cutoff = now - (self._window_minutes * 60 * 1000)
        while self._rewind_events and self._rewind_events[0] < cutoff:
            self._rewind_events.popleft()

        rewind_count = len(self._rewind_events)
        window_minutes = self._window_minutes
        rewinds_per_minute = rewind_count / window_minutes if window_minutes > 0 else 0.0

        # Burst detection: 3+ rewinds in 60 seconds
        burst_detected = False
        rewind_list = list(self._rewind_events)
        burst_window_ms = self._burst_window_seconds * 1000
        for i in range(len(rewind_list)):
            count_in_window = sum(
                1 for j in range(i, len(rewind_list))
                if rewind_list[j] - rewind_list[i] <= burst_window_ms
            )
            if count_in_window >= self._burst_threshold:
                burst_detected = True
                break

        # Repeated segments
        repeated = [seg for seg, cnt in self._segment_rewinds.items() if cnt >= 2]

        self._result = RewindResult(
            rewinds_per_minute=round(rewinds_per_minute, 2),
            rewind_burst_detected=burst_detected,
            repeated_segment_ids=repeated,
        )
        logger.debug("Rewind: {}/min, burst={}, repeated={}", rewinds_per_minute, burst_detected, repeated)
        return self._result

    def get_current_value(self) -> dict[str, float]:
        return {
            "rewinds_per_minute": self._result.rewinds_per_minute,
            "rewind_burst": 1.0 if self._result.rewind_burst_detected else 0.0,
        }

    def reset(self) -> None:
        self._rewind_events.clear()
        self._segment_rewinds.clear()
        self._result = RewindResult()


# =============================================================================
# IdleSignal
# =============================================================================

class IdleSignal:
    """
    Tracks idle periods and patterns.

    Window: All idle events in current session, with trend computed
    over a 5-minute rolling window.
    """

    def __init__(self) -> None:
        self._window_minutes = get_threshold("IDLE_WINDOW_MINUTES")
        self._all_idles: list[tuple[float, float]] = []  # (timestamp, duration_ms)
        self._result = IdleResult()

    def process(self, events: list[RawEvent]) -> IdleResult:
        """Process idle events and compute idle metrics."""
        for event in events:
            if isinstance(event, IdleEvent):
                self._all_idles.append((event.timestamp, event.idle_duration_ms))

        if not self._all_idles:
            self._result = IdleResult()
            return self._result

        total_idle = sum(d for _, d in self._all_idles)
        longest_idle = max(d for _, d in self._all_idles)

        # Idle frequency: idles per minute over recent window
        now = time.time() * 1000.0
        window_ms = self._window_minutes * 60 * 1000
        recent = [(t, d) for t, d in self._all_idles if t >= now - window_ms]
        idle_frequency = len(recent) / self._window_minutes if self._window_minutes > 0 else 0.0

        # Trend: compare idle frequency in last 2 min vs prior 3 min
        trend = "stable"
        two_min_ms = 2 * 60 * 1000
        three_min_ms = 3 * 60 * 1000
        recent_2min = sum(1 for t, _ in self._all_idles if t >= now - two_min_ms)
        prior_3min = sum(
            1 for t, _ in self._all_idles
            if now - (two_min_ms + three_min_ms) <= t < now - two_min_ms
        )
        # Normalise by time window
        recent_rate = recent_2min / 2.0
        prior_rate = prior_3min / 3.0 if prior_3min > 0 else 0.0
        if prior_rate > 0 and recent_rate > prior_rate * 1.3:
            trend = "increasing"

        self._result = IdleResult(
            total_idle_time_ms=round(total_idle, 1),
            idle_frequency=round(idle_frequency, 2),
            longest_idle_ms=round(longest_idle, 1),
            recent_idle_trend=trend,  # type: ignore[arg-type]
        )
        logger.debug("Idle: total={}ms, freq={}/min, trend={}", total_idle, idle_frequency, trend)
        return self._result

    def get_current_value(self) -> dict[str, float]:
        return {
            "idle_frequency": self._result.idle_frequency,
            "total_idle_time_ms": self._result.total_idle_time_ms,
        }

    def reset(self) -> None:
        self._all_idles.clear()
        self._result = IdleResult()


# =============================================================================
# InteractionVarianceSignal
# =============================================================================

class InteractionVarianceSignal:
    """
    Detects erratic interaction patterns — the KEY fatigue signal.

    A tired brain doesn't slow down (that's visible), it becomes ERRATIC.
    Variance catches fatigue before the student even feels it.
    """

    def __init__(self) -> None:
        self._window_size = int(get_threshold("INTERACTION_VARIANCE_WINDOW"))
        self._threshold = get_threshold("FATIGUE_VARIANCE_THRESHOLD")
        self._timestamps: deque[float] = deque(maxlen=self._window_size)
        self._result = InteractionVarianceResult()

    def process(self, events: list[RawEvent]) -> InteractionVarianceResult:
        """Process any events and compute interaction variance."""
        for event in events:
            self._timestamps.append(event.timestamp)

        if len(self._timestamps) < 3:
            self._result = InteractionVarianceResult()
            return self._result

        ts = list(self._timestamps)
        intervals = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]

        if not intervals:
            self._result = InteractionVarianceResult()
            return self._result

        mean_interval = float(np.mean(intervals))
        if mean_interval == 0:
            variance = 0.0
        else:
            # Coefficient of variation
            variance = float(scipy_stats.variation(intervals))

        # Trend
        if variance > self._threshold * 1.5:
            trend = "erratic"
        elif variance > self._threshold:
            trend = "increasing"
        else:
            trend = "stable"

        # Fatigue probability via sigmoid
        fatigue_prob = _sigmoid(variance - self._threshold)

        self._result = InteractionVarianceResult(
            interaction_variance=round(variance, 4),
            variance_trend=trend,  # type: ignore[arg-type]
            fatigue_probability=round(fatigue_prob, 3),
        )
        logger.debug("Variance: cv={}, trend={}, fatigue_p={}", variance, trend, fatigue_prob)
        return self._result

    def get_current_value(self) -> dict[str, float]:
        return {
            "interaction_variance": self._result.interaction_variance,
            "fatigue_probability": self._result.fatigue_probability,
        }

    def reset(self) -> None:
        self._timestamps.clear()
        self._result = InteractionVarianceResult()


# =============================================================================
# ScrollBehaviorSignal
# =============================================================================

class ScrollBehaviorSignal:
    """
    Detects rushed scrolling (boredom) vs slow scrolling (engagement).

    Window: Last 30 scroll events.
    """

    def __init__(self) -> None:
        self._window_size = int(get_threshold("SCROLL_WINDOW"))
        self._scroll_events: deque[tuple[float, float]] = deque(maxlen=self._window_size)
        self._result = ScrollResult()

    def process(self, events: list[RawEvent]) -> ScrollResult:
        """Process scroll events and classify scroll pattern."""
        for event in events:
            if event.event_type == "scroll":
                scroll_y = event.metadata.get("scroll_y", 0.0)
                self._scroll_events.append((event.timestamp, float(scroll_y)))

        if len(self._scroll_events) < 2:
            self._result = ScrollResult()
            return self._result

        scrolls = list(self._scroll_events)
        speeds: list[float] = []
        pauses = 0
        for i in range(1, len(scrolls)):
            dt = (scrolls[i][0] - scrolls[i - 1][0]) / 1000.0  # seconds
            if dt <= 0:
                continue
            dy = abs(scrolls[i][1] - scrolls[i - 1][1])
            speed = dy / dt  # pixels per second
            speeds.append(speed)
            if dt > 2.0:  # pause > 2 seconds
                pauses += 1

        if not speeds:
            self._result = ScrollResult()
            return self._result

        mean_speed = float(np.mean(speeds))
        rapid_bursts = sum(1 for s in speeds if s > 2000)  # very fast scrolling

        # Pattern classification
        if mean_speed > 1500 and pauses == 0:
            pattern = SCROLL_RUSHING
        elif mean_speed > 800:
            pattern = SCROLL_SKIMMING
        else:
            pattern = SCROLL_ENGAGED

        self._result = ScrollResult(
            mean_scroll_speed=round(mean_speed, 1),
            scroll_pattern=pattern,  # type: ignore[arg-type]
            rapid_scroll_bursts=rapid_bursts,
        )
        logger.debug("Scroll: speed={}, pattern={}, bursts={}", mean_speed, pattern, rapid_bursts)
        return self._result

    def get_current_value(self) -> dict[str, float]:
        return {
            "mean_scroll_speed": self._result.mean_scroll_speed,
            "rapid_scroll_bursts": float(self._result.rapid_scroll_bursts),
        }

    def reset(self) -> None:
        self._scroll_events.clear()
        self._result = ScrollResult()


# =============================================================================
# SessionPacingSignal
# =============================================================================

class SessionPacingSignal:
    """
    Overall session pace tracker — used by M12 (circadian).

    Window: Entire session.
    """

    def __init__(self, session_start_ms: float) -> None:
        self._session_start = session_start_ms
        self._interaction_timestamps: list[float] = []
        self._quiz_scores_first_half: list[float] = []
        self._quiz_scores_second_half: list[float] = []
        self._fatigue_first_crossed: float | None = None
        self._result = SessionPacingResult()

    def process(self, events: list[RawEvent]) -> SessionPacingResult:
        """Process events and compute session pacing metrics."""
        for event in events:
            self._interaction_timestamps.append(event.timestamp)
            if isinstance(event, QuestionEvent) and event.answer_correct is not None:
                score = 1.0 if event.answer_correct else 0.0
                midpoint = self._session_start + (event.timestamp - self._session_start) / 2
                if event.timestamp < midpoint + self._session_start:
                    self._quiz_scores_first_half.append(score)
                else:
                    self._quiz_scores_second_half.append(score)

        now = time.time() * 1000.0
        duration_ms = now - self._session_start
        duration_min = duration_ms / 60000.0

        # Engagement: active interaction time / total time
        active_count = len(self._interaction_timestamps)
        engagement = min(1.0, active_count / max(1.0, duration_min * 4))  # ~4 events/min = full engagement

        # Performance trajectory
        trajectory = "stable"
        if self._quiz_scores_first_half and self._quiz_scores_second_half:
            first_avg = float(np.mean(self._quiz_scores_first_half))
            second_avg = float(np.mean(self._quiz_scores_second_half))
            if second_avg > first_avg + 0.15:
                trajectory = "improving"
            elif second_avg < first_avg - 0.15:
                trajectory = "declining"

        # Optimal session estimate: default 30 min, adjusted by fatigue
        optimal = 30.0

        self._result = SessionPacingResult(
            session_duration_minutes=round(duration_min, 1),
            content_engagement_rate=round(engagement, 3),
            performance_trajectory=trajectory,  # type: ignore[arg-type]
            optimal_session_length_estimate=optimal,
        )
        return self._result

    def get_current_value(self) -> dict[str, float]:
        return {
            "session_duration_minutes": self._result.session_duration_minutes,
            "content_engagement_rate": self._result.content_engagement_rate,
        }

    def reset(self) -> None:
        self._interaction_timestamps.clear()
        self._quiz_scores_first_half.clear()
        self._quiz_scores_second_half.clear()
        self._result = SessionPacingResult()


# =============================================================================
# Utility
# =============================================================================

def _sigmoid(x: float) -> float:
    """Sigmoid function clamped to avoid overflow."""
    x = max(-10.0, min(10.0, x * 5.0))
    return 1.0 / (1.0 + math.exp(-x))
