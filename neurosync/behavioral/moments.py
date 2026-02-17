"""
NeuroSync AI — Moment detectors.

These consume processed signals and output moment flags for:
  M07: Silent frustration / pre-dropout
  M08: Insight moment (behavioral proxy)
  M10: Mental fatigue (interaction variance)
  M14: Pseudo-understanding
  M20: Dopamine crash (variable ratio rewards)
"""

from __future__ import annotations

import random
import time
from typing import Optional

from loguru import logger

from neurosync.config.settings import get_threshold
from neurosync.core.constants import (
    FATIGUE_CRITICAL,
    FATIGUE_FRESH,
    FATIGUE_MILD,
    FATIGUE_TIRED,
    FRUSTRATION_CRITICAL,
    FRUSTRATION_NONE,
    FRUSTRATION_WARNING,
    FRUSTRATION_WATCH,
    MASTERY_ACCEPT,
    MASTERY_FLAG,
    MASTERY_PROBE,
    REWARD_TYPES,
)
from neurosync.core.events import (
    FatigueResult,
    FrustrationResult,
    InsightResult,
    MasteryCheckResult,
    QuestionEvent,
    RewardDecision,
)


# =============================================================================
# M07 — Frustration Detector
# =============================================================================

class FrustrationDetector:
    """
    Composite frustration score that predicts dropout risk.

    Score formula (weighted, 0.0 to 1.0):
        score = (
            rewind_burst_detected * 0.30 +
            response_time_trend_increasing * 0.25 +
            idle_trend_increasing * 0.20 +
            facial_tension * 0.15 +           # 0.0 until Step 2
            eeg_theta_high * 0.10             # 0.0 until Step 10
        )
    """

    def __init__(self) -> None:
        self._watch = get_threshold("FRUSTRATION_WATCH_THRESHOLD")
        self._warning = get_threshold("FRUSTRATION_WARNING_THRESHOLD")
        self._critical = get_threshold("FRUSTRATION_CRITICAL_THRESHOLD")
        self._cooldown_sec = get_threshold("FRUSTRATION_COOLDOWN_SECONDS")
        self._last_intervention_time: float = 0.0

    def detect(
        self,
        rewind_burst: bool = False,
        response_time_trend: str = "stable",
        idle_trend: str = "stable",
        facial_tension: float = 0.0,
        eeg_theta_high: float = 0.0,
    ) -> FrustrationResult:
        """Compute composite frustration score from available signals."""

        rewind_score = 1.0 if rewind_burst else 0.0
        rt_score = 1.0 if response_time_trend == "increasing" else 0.0
        idle_score = 1.0 if idle_trend == "increasing" else 0.0

        score = (
            rewind_score * 0.30
            + rt_score * 0.25
            + idle_score * 0.20
            + facial_tension * 0.15
            + eeg_theta_high * 0.10
        )
        score = min(1.0, max(0.0, score))

        # Determine level
        if score > self._critical:
            level = FRUSTRATION_CRITICAL
        elif score > self._warning:
            level = FRUSTRATION_WARNING
        elif score > self._watch:
            level = FRUSTRATION_WATCH
        else:
            level = FRUSTRATION_NONE

        # Dominant signal
        contributions = {
            "rewind_burst": rewind_score * 0.30,
            "response_time": rt_score * 0.25,
            "idle_trend": idle_score * 0.20,
            "facial_tension": facial_tension * 0.15,
            "eeg_theta": eeg_theta_high * 0.10,
        }
        dominant = max(contributions, key=contributions.get)  # type: ignore[arg-type]

        # Recommended action
        actions = {
            FRUSTRATION_NONE: "continue_monitoring",
            FRUSTRATION_WATCH: "increase_monitoring_frequency",
            FRUSTRATION_WARNING: "prepare_method_switch",
            FRUSTRATION_CRITICAL: "fire_rescue_intervention",
        }
        action = actions[level]

        # Confidence: higher when more signals agree
        active_signals = sum(1 for v in contributions.values() if v > 0)
        confidence = min(1.0, active_signals / 3.0)

        result = FrustrationResult(
            score=round(score, 3),
            level=level,  # type: ignore[arg-type]
            dominant_signal=dominant,
            recommended_action=action,
            confidence=round(confidence, 2),
        )
        logger.debug("Frustration: score={}, level={}, dominant={}", score, level, dominant)
        return result

    def should_intervene(self, result: FrustrationResult) -> bool:
        """Check if an intervention should fire (respecting cooldown)."""
        if result.level not in (FRUSTRATION_WARNING, FRUSTRATION_CRITICAL):
            return False
        now = time.time()
        if now - self._last_intervention_time < self._cooldown_sec:
            logger.debug("Frustration intervention blocked by cooldown")
            return False
        self._last_intervention_time = now
        return True


# =============================================================================
# M10 — Fatigue Detector
# =============================================================================

class FatigueDetector:
    """
    Detects cognitive fatigue via interaction variance.

    Key insight: Fatigue shows as ERRATIC behavior, not just SLOW behavior.
    """

    def __init__(self) -> None:
        self._soft = get_threshold("FATIGUE_SOFT_THRESHOLD")
        self._mandatory = get_threshold("FATIGUE_MANDATORY_THRESHOLD")
        self._risk_start = get_threshold("FATIGUE_SESSION_RISK_START_MINUTES")
        self._risk_full = get_threshold("FATIGUE_SESSION_RISK_FULL_MINUTES")
        self._break_cooldown_min = get_threshold("FATIGUE_BREAK_COOLDOWN_MINUTES")
        self._last_break_time: float = 0.0

    def detect(
        self,
        interaction_variance: float = 0.0,
        session_duration_minutes: float = 0.0,
        idle_frequency: float = 0.0,
        performance_decline: float = 0.0,
    ) -> FatigueResult:
        """Compute fatigue score from signals."""

        # Normalize interaction variance (0-1)
        variance_norm = min(1.0, interaction_variance / 1.5)

        # Session duration factor
        if session_duration_minutes <= self._risk_start:
            duration_factor = 0.0
        elif session_duration_minutes >= self._risk_full:
            duration_factor = 1.0
        else:
            duration_factor = (session_duration_minutes - self._risk_start) / (
                self._risk_full - self._risk_start
            )

        # Idle frequency normalised (assuming >3/min is high)
        idle_norm = min(1.0, idle_frequency / 3.0)

        # Performance decline normalised
        perf_norm = min(1.0, max(0.0, performance_decline))

        score = (
            variance_norm * 0.50
            + duration_factor * 0.25
            + idle_norm * 0.15
            + perf_norm * 0.10
        )
        score = min(1.0, max(0.0, score))

        # Level
        if score >= self._mandatory:
            level = FATIGUE_CRITICAL
        elif score > self._soft:
            level = FATIGUE_TIRED
        elif score > 0.25:
            level = FATIGUE_MILD
        else:
            level = FATIGUE_FRESH

        # Estimate minutes until critical
        est_min: Optional[float] = None
        if score < self._mandatory and score > 0.1:
            # Linear extrapolation (rough)
            rate = score / max(1.0, session_duration_minutes)
            if rate > 0:
                remaining = (self._mandatory - score) / rate
                est_min = round(remaining, 1)

        break_recommended = score >= self._soft
        break_mandatory = score >= self._mandatory

        result = FatigueResult(
            score=round(score, 3),
            level=level,  # type: ignore[arg-type]
            session_minutes_elapsed=round(session_duration_minutes, 1),
            estimated_minutes_until_critical=est_min,
            break_recommended=break_recommended,
            break_mandatory=break_mandatory,
        )
        logger.debug("Fatigue: score={}, level={}, break_mandatory={}", score, level, break_mandatory)
        return result

    def should_force_break(self, result: FatigueResult) -> bool:
        """Check if a mandatory break should fire (respecting cooldown)."""
        if not result.break_mandatory:
            return False
        now = time.time()
        cooldown_sec = self._break_cooldown_min * 60
        if now - self._last_break_time < cooldown_sec:
            logger.debug("Fatigue break blocked by cooldown")
            return False
        self._last_break_time = now
        return True


# =============================================================================
# M14 — Pseudo-Understanding Detector
# =============================================================================

class PseudoUnderstandingDetector:
    """
    Detects when a correct answer is likely guessed or shallowly processed.
    """

    def __init__(self) -> None:
        self._fast_threshold = get_threshold("FAST_ANSWER_THRESHOLD_MS")
        self._slow_threshold = get_threshold("SLOW_ANSWER_THRESHOLD_MS")
        self._flagged_concepts: set[str] = set()

    def check(self, event: QuestionEvent) -> MasteryCheckResult:
        """Check authenticity of a question answer."""

        answer_correct = event.answer_correct or False
        response_time = event.response_time_ms or 0.0
        confidence = event.confidence_score or 3

        # Time score: 0 if <3s, 1.0 if >15s, linear between
        if response_time <= self._fast_threshold:
            time_score = 0.0
        elif response_time >= self._slow_threshold:
            time_score = 1.0
        else:
            time_score = (response_time - self._fast_threshold) / (
                self._slow_threshold - self._fast_threshold
            )

        # Confidence score normalised (1-5 → 0.0-1.0)
        confidence_norm = (confidence - 1) / 4.0

        # Graph consistency: 0.0 until Step 3 adds Neo4j
        graph_consistency = 0.0

        # Composite authenticity
        authenticity = (
            time_score * 0.40
            + confidence_norm * 0.30
            + graph_consistency * 0.30
        )

        # Determine flag
        if authenticity < 0.35:
            flag = MASTERY_FLAG
            reason = f"Suspiciously fast ({response_time:.0f}ms) and/or low confidence ({confidence}/5)"
            if response_time < self._fast_threshold and answer_correct:
                action = "require_elaboration"
            else:
                action = "schedule_delayed_retest"
        elif authenticity < 0.60:
            flag = MASTERY_PROBE
            reason = f"Moderate authenticity ({authenticity:.2f}) — follow-up recommended"
            action = "ask_followup"
        else:
            flag = MASTERY_ACCEPT
            reason = f"Strong authenticity ({authenticity:.2f}) — genuine understanding"
            action = "accept_mastery"

        # Track flagged concepts (once per session per concept)
        if flag == MASTERY_FLAG:
            self._flagged_concepts.add(event.concept_id)

        result = MasteryCheckResult(
            question_id=event.question_id,
            concept_id=event.concept_id,
            answer_correct=answer_correct,
            authenticity_score=round(authenticity, 3),
            flag=flag,  # type: ignore[arg-type]
            reason=reason,
            recommended_action=action,  # type: ignore[arg-type]
        )
        logger.debug(
            "M14: q={}, correct={}, authenticity={}, flag={}",
            event.question_id, answer_correct, authenticity, flag,
        )
        return result


# =============================================================================
# M08 — Insight Detector (Behavioral Proxy)
# =============================================================================

class InsightDetector:
    """
    Detects potential insight moments from behavioral signals.

    Behavioral signature: STRUGGLE → RESOLUTION → ENERGY
    """

    def __init__(self) -> None:
        self._frustration_threshold = get_threshold("INSIGHT_PRECEDING_FRUSTRATION_THRESHOLD")
        self._preceding_duration_sec = get_threshold("INSIGHT_PRECEDING_DURATION_SECONDS")
        self._resolution_speed_ms = get_threshold("INSIGHT_RESOLUTION_SPEED_MS")
        self._window_duration_sec = get_threshold("INSIGHT_WINDOW_DURATION_SECONDS")
        self._cooldown_min = get_threshold("INSIGHT_COOLDOWN_MINUTES")
        self._frustration_history: list[tuple[float, float]] = []  # (timestamp_sec, score)
        self._last_insight_time: float = 0.0

    def record_frustration(self, timestamp_sec: float, score: float) -> None:
        """Record a frustration score sample for insight detection."""
        self._frustration_history.append((timestamp_sec, score))
        # Keep only last 5 minutes
        cutoff = timestamp_sec - 300
        self._frustration_history = [
            (t, s) for t, s in self._frustration_history if t >= cutoff
        ]

    def check_insight(
        self,
        event: QuestionEvent,
        post_interaction_speeds: list[float] | None = None,
    ) -> InsightResult:
        """
        Check if a correct answer represents an insight moment.

        Args:
            event: The question event (must be correct and fast).
            post_interaction_speeds: Times (ms) of the next 3 interactions.
                                     If faster than baseline, energy surge confirmed.
        """
        if not event.answer_correct:
            return InsightResult()

        response_time = event.response_time_ms or float("inf")
        if response_time > self._resolution_speed_ms:
            return InsightResult()

        # Check for preceding struggle
        now_sec = event.timestamp / 1000.0
        struggle_start = now_sec - self._preceding_duration_sec
        frustration_during = [
            s for t, s in self._frustration_history
            if t >= struggle_start and s >= self._frustration_threshold
        ]

        if len(frustration_during) < 2:
            return InsightResult()

        # Check cooldown
        if now_sec - self._last_insight_time < self._cooldown_min * 60:
            return InsightResult()

        # Compute struggle duration
        first_struggle = min(t for t, s in self._frustration_history if s >= self._frustration_threshold and t >= struggle_start)
        struggle_duration_ms = (now_sec - first_struggle) * 1000

        # Energy surge check (optional — may not have post-interaction data yet)
        energy_confirmed = True  # default true for behavioral proxy
        if post_interaction_speeds and len(post_interaction_speeds) >= 2:
            baseline = response_time  # use the resolution speed as baseline
            faster = sum(1 for s in post_interaction_speeds if s < baseline * 1.2)
            energy_confirmed = faster >= 2

        if not energy_confirmed:
            return InsightResult()

        # Insight detected!
        self._last_insight_time = now_sec
        confidence = min(1.0, len(frustration_during) / 5.0)

        result = InsightResult(
            detected=True,
            confidence=round(confidence, 2),
            window_open_until=now_sec + self._window_duration_sec,
            preceding_struggle_duration_ms=round(struggle_duration_ms, 1),
            recommended_chain_concept_count=min(3, max(2, int(confidence * 3))),
        )
        logger.info("INSIGHT DETECTED! confidence={}, struggle={}ms", confidence, struggle_duration_ms)
        return result


# =============================================================================
# M20 — Variable Reward Scheduler
# =============================================================================

class VariableRewardScheduler:
    """
    Implements Skinner's Variable Ratio reward schedule.

    Rewards fire at unpredictable intervals to maintain motivation.
    """

    def __init__(self) -> None:
        self._min_interval = int(get_threshold("REWARD_MIN_INTERVAL_ANSWERS"))
        self._max_interval = int(get_threshold("REWARD_MAX_INTERVAL_ANSWERS"))
        self._motivation_dip = get_threshold("REWARD_MOTIVATION_DIP_THRESHOLD")
        self._cooldown_min = get_threshold("REWARD_COOLDOWN_MINUTES")
        self._max_gap_min = get_threshold("REWARD_MAX_GAP_MINUTES")

        self._correct_since_last_reward = 0
        self._next_reward_at = random.randint(self._min_interval, self._max_interval)
        self._last_reward_time: float = 0.0
        self._total_rewards = 0

    def record_correct_answer(
        self,
        interaction_speed_ratio: float = 1.0,
        current_time: Optional[float] = None,
    ) -> RewardDecision:
        """
        Record a correct answer and decide whether to fire a reward.

        Args:
            interaction_speed_ratio: Current speed / baseline speed. <0.8 = motivation dip.
            current_time: Current time in seconds (defaults to now).
        """
        now = current_time or time.time()
        self._correct_since_last_reward += 1

        # Check cooldown
        cooldown_sec = self._cooldown_min * 60
        if self._last_reward_time > 0 and (now - self._last_reward_time) < cooldown_sec:
            return RewardDecision(
                fire_reward=False,
                reason="Cooldown active",
                next_check_after_ms=int((cooldown_sec - (now - self._last_reward_time)) * 1000),
            )

        fire = False
        reason = ""

        # Regular schedule
        if self._correct_since_last_reward >= self._next_reward_at:
            fire = True
            reason = f"Variable ratio schedule: {self._correct_since_last_reward} correct answers"

        # Motivation dip override
        elif interaction_speed_ratio < self._motivation_dip and self._correct_since_last_reward >= 3:
            fire = True
            reason = f"Motivation dip detected (speed ratio: {interaction_speed_ratio:.2f})"

        # Max gap override
        elif self._last_reward_time > 0 and (now - self._last_reward_time) > self._max_gap_min * 60:
            fire = True
            reason = f"Max gap exceeded ({self._max_gap_min} minutes)"

        if fire:
            reward_type = random.choice(REWARD_TYPES)
            self._correct_since_last_reward = 0
            self._next_reward_at = random.randint(self._min_interval, self._max_interval)
            self._last_reward_time = now
            self._total_rewards += 1

            return RewardDecision(
                fire_reward=True,
                reward_type=reward_type,
                reason=reason,
                next_check_after_ms=int(cooldown_sec * 1000),
            )

        return RewardDecision(
            fire_reward=False,
            reason="Threshold not reached",
            next_check_after_ms=5000,
        )
