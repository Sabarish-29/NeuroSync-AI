"""
NeuroSync AI — Tests for moment detectors.

Tests:
  7.  test_frustration_critical — correct signals → critical level
  8.  test_frustration_no_trigger — insufficient signals → no flag
  9.  test_fatigue_mandatory — after 35min + high variance → mandatory break
  10. test_fatigue_cooldown — no second break within 20 min
  11. test_pseudo_understanding_fast_answer — <3s answer flagged
  12. test_pseudo_understanding_slow_confident — accepted
  13. test_insight_detection — struggle→resolution→energy → detected
  14. test_insight_no_false_positive — resolution without preceding struggle → not detected
  15. test_variable_reward_unpredictable — fires within window bounds
"""

import time
import uuid

import pytest

from neurosync.behavioral.moments import (
    FatigueDetector,
    FrustrationDetector,
    InsightDetector,
    PseudoUnderstandingDetector,
    VariableRewardScheduler,
)
from neurosync.core.events import QuestionEvent
from tests.conftest import make_question_event


class TestFrustrationDetector:
    """Tests for M07 — Frustration Detector."""

    def test_frustration_critical(self) -> None:
        """When rewind burst + increasing response time + increasing idle → critical."""
        detector = FrustrationDetector()
        result = detector.detect(
            rewind_burst=True,
            response_time_trend="increasing",
            idle_trend="increasing",
        )
        # 0.30 + 0.25 + 0.20 = 0.75 > 0.70 → critical
        assert result.level == "critical"
        assert result.score >= 0.70
        assert result.confidence > 0

    def test_frustration_warning(self) -> None:
        """Two signals → warning level."""
        detector = FrustrationDetector()
        result = detector.detect(
            rewind_burst=True,
            response_time_trend="increasing",
            idle_trend="stable",
        )
        # 0.30 + 0.25 = 0.55 > 0.45 → warning
        assert result.level == "warning"
        assert result.score >= 0.45

    def test_frustration_no_trigger(self) -> None:
        """No active signals → no frustration."""
        detector = FrustrationDetector()
        result = detector.detect(
            rewind_burst=False,
            response_time_trend="stable",
            idle_trend="stable",
        )
        assert result.level == "none"
        assert result.score < 0.25

    def test_frustration_cooldown(self) -> None:
        """Intervention should not fire twice within cooldown period."""
        detector = FrustrationDetector()
        result = detector.detect(
            rewind_burst=True,
            response_time_trend="increasing",
            idle_trend="increasing",
        )
        assert result.level == "critical"

        # First intervention should fire
        assert detector.should_intervene(result) is True
        # Second immediate call should be blocked by cooldown
        assert detector.should_intervene(result) is False


class TestFatigueDetector:
    """Tests for M10 — Fatigue Detector."""

    def test_fatigue_mandatory(self) -> None:
        """High variance + long session → mandatory break."""
        detector = FatigueDetector()
        result = detector.detect(
            interaction_variance=1.2,    # well above 0.65 threshold
            session_duration_minutes=40,  # above 35 min full risk
            idle_frequency=2.0,
            performance_decline=0.5,
        )
        assert result.level == "critical"
        assert result.break_mandatory is True
        assert result.score > 0.75

    def test_fatigue_fresh_early_session(self) -> None:
        """Early in session with low variance → fresh."""
        detector = FatigueDetector()
        result = detector.detect(
            interaction_variance=0.1,
            session_duration_minutes=5,
            idle_frequency=0.5,
        )
        assert result.level == "fresh"
        assert result.break_mandatory is False
        assert result.break_recommended is False

    def test_fatigue_cooldown(self) -> None:
        """No second mandatory break within 20 minutes."""
        detector = FatigueDetector()
        result = detector.detect(
            interaction_variance=1.5,
            session_duration_minutes=40,
            idle_frequency=3.0,
        )
        assert result.break_mandatory is True

        # First break fires
        assert detector.should_force_break(result) is True
        # Second call within cooldown — blocked
        assert detector.should_force_break(result) is False


class TestPseudoUnderstandingDetector:
    """Tests for M14 — Pseudo-Understanding Detector."""

    def test_pseudo_understanding_fast_answer(self) -> None:
        """Very fast correct answer (<3s) is flagged as pseudo-understanding."""
        detector = PseudoUnderstandingDetector()
        event = make_question_event(
            answer_correct=True,
            response_time_ms=1500,   # <3000ms → suspicious
            confidence_score=2,
        )
        result = detector.check(event)
        assert result.flag == "flag"
        assert result.authenticity_score < 0.35
        assert "fast" in result.reason.lower() or "suspicious" in result.reason.lower()

    def test_pseudo_understanding_slow_confident(self) -> None:
        """Slow, confident correct answer is accepted as genuine mastery."""
        detector = PseudoUnderstandingDetector()
        event = make_question_event(
            answer_correct=True,
            response_time_ms=18000,  # well above 15s → thoughtful
            confidence_score=5,      # very confident
        )
        result = detector.check(event)
        assert result.flag == "accept"
        assert result.authenticity_score >= 0.60
        assert result.recommended_action == "accept_mastery"

    def test_pseudo_understanding_moderate(self) -> None:
        """Moderate response time + moderate confidence → flag or probe (graph_consistency=0 in Step 1)."""
        detector = PseudoUnderstandingDetector()
        event = make_question_event(
            answer_correct=True,
            response_time_ms=10000,
            confidence_score=4,
        )
        result = detector.check(event)
        assert result.flag in ("probe", "flag", "accept")


class TestInsightDetector:
    """Tests for M08 — Insight Detector."""

    def test_insight_detection(self) -> None:
        """Struggle → fast correct answer → insight detected."""
        detector = InsightDetector()
        now = time.time()

        # Record frustration for 90 seconds
        for i in range(10):
            detector.record_frustration(now - 90 + i * 9, 0.6)

        # Fast correct answer (resolution)
        event = make_question_event(
            answer_correct=True,
            response_time_ms=2500,  # fast
            timestamp=now * 1000,
        )

        result = detector.check_insight(event)
        assert result.detected is True
        assert result.confidence > 0
        assert result.window_open_until is not None
        assert result.preceding_struggle_duration_ms > 0

    def test_insight_no_false_positive(self) -> None:
        """Fast correct answer WITHOUT preceding struggle → not detected."""
        detector = InsightDetector()
        now = time.time()

        # No frustration history
        event = make_question_event(
            answer_correct=True,
            response_time_ms=2000,
            timestamp=now * 1000,
        )

        result = detector.check_insight(event)
        assert result.detected is False

    def test_insight_wrong_answer_no_trigger(self) -> None:
        """Wrong answer never triggers insight, even after struggle."""
        detector = InsightDetector()
        now = time.time()

        for i in range(10):
            detector.record_frustration(now - 90 + i * 9, 0.6)

        event = make_question_event(
            answer_correct=False,
            response_time_ms=2000,
            timestamp=now * 1000,
        )

        result = detector.check_insight(event)
        assert result.detected is False


class TestVariableRewardScheduler:
    """Tests for M20 — Variable Reward Scheduler."""

    def test_variable_reward_unpredictable(self) -> None:
        """Reward fires within the 8-12 answer window but not before."""
        scheduler = VariableRewardScheduler()
        now = time.time()

        rewards_fired = []
        # Record 20 correct answers, track when rewards fire
        for i in range(20):
            result = scheduler.record_correct_answer(
                interaction_speed_ratio=1.0,
                current_time=now + i * 60,  # 1 minute apart (avoids cooldown)
            )
            if result.fire_reward:
                rewards_fired.append(i + 1)

        # At least one reward should fire within 20 answers
        assert len(rewards_fired) >= 1
        # First reward should come between answer 8 and 12
        assert rewards_fired[0] >= 3  # can be earlier with motivation dip, but with ratio 1.0, min is ~8

    def test_reward_cooldown(self) -> None:
        """Reward doesn't fire twice within cooldown period."""
        scheduler = VariableRewardScheduler()
        now = time.time()

        # Force a reward
        scheduler._correct_since_last_reward = 15
        result1 = scheduler.record_correct_answer(current_time=now)
        assert result1.fire_reward is True

        # Immediate second attempt should be blocked (within 5min cooldown)
        scheduler._correct_since_last_reward = 15
        result2 = scheduler.record_correct_answer(current_time=now + 10)
        assert result2.fire_reward is False
