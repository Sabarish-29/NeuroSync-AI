"""
NeuroSync AI — Multi-signal behavioral fusion engine.

The central coordinator. Runs every 500ms during a session.
Collects all signal results and outputs moment flags.

Decision rules:
    HIGH CONFIDENCE (3+ signals agree) → Fire intervention immediately
    MEDIUM CONFIDENCE (2 signals agree) → Fire soft intervention
    LOW CONFIDENCE (1 signal) → Log only, no action

Cooldown rules:
    M07 (rescue): minimum 5 minutes between interventions
    M10 (break): minimum 20 minutes between forced breaks
    M14 (elaboration): per-concept, once per session
    M08 (insight): minimum 10 minutes between chainings
    M20 (reward): minimum 5 minutes between rewards
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

from loguru import logger

from neurosync.behavioral.moments import (
    FatigueDetector,
    FrustrationDetector,
    InsightDetector,
    PseudoUnderstandingDetector,
    VariableRewardScheduler,
)
from neurosync.behavioral.signals import (
    IdleSignal,
    InteractionVarianceSignal,
    ResponseTimeSignal,
    RewindSignal,
    ScrollBehaviorSignal,
    SessionPacingSignal,
)
from neurosync.config.settings import get_threshold
from neurosync.core.constants import (
    MOMENT_DOPAMINE_CRASH,
    MOMENT_FATIGUE,
    MOMENT_FRUSTRATION,
    MOMENT_INSIGHT,
    MOMENT_PSEUDO_UNDERSTANDING,
    URGENCY_DEFERRED,
    URGENCY_IMMEDIATE,
    URGENCY_NEXT_PAUSE,
)
from neurosync.core.events import (
    InterventionRequest,
    MomentFlags,
    QuestionEvent,
    RawEvent,
)
from neurosync.database.manager import DatabaseManager
from neurosync.database.repositories.signals import SignalRepository


class BehavioralFusionEngine:
    """
    Central fusion engine that coordinates all signal processors and moment
    detectors, producing unified moment flags every fusion cycle.
    """

    def __init__(
        self,
        session_id: str,
        session_start_ms: float,
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        self._session_id = session_id
        self._session_start_ms = session_start_ms

        # Signal processors
        self._response_time = ResponseTimeSignal()
        self._rewind = RewindSignal()
        self._idle = IdleSignal()
        self._interaction_variance = InteractionVarianceSignal()
        self._scroll = ScrollBehaviorSignal()
        self._session_pacing = SessionPacingSignal(session_start_ms)

        # Moment detectors
        self._frustration_detector = FrustrationDetector()
        self._fatigue_detector = FatigueDetector()
        self._pseudo_understanding = PseudoUnderstandingDetector()
        self._insight_detector = InsightDetector()
        self._reward_scheduler = VariableRewardScheduler()

        # Database (optional — can run without persistence)
        self._signal_repo: Optional[SignalRepository] = None
        if db_manager is not None:
            self._signal_repo = SignalRepository(db_manager)

        # Event buffer for batch processing
        self._event_buffer: list[RawEvent] = []
        self._running = False

        # Intervention log
        self._interventions_fired: list[InterventionRequest] = []
        self._cycle_count = 0

        logger.info("BehavioralFusionEngine initialised for session {}", session_id)

    @property
    def interventions_fired(self) -> list[InterventionRequest]:
        """All interventions fired during this session."""
        return list(self._interventions_fired)

    @property
    def frustration_detector(self) -> FrustrationDetector:
        return self._frustration_detector

    @property
    def fatigue_detector(self) -> FatigueDetector:
        return self._fatigue_detector

    @property
    def pseudo_understanding_detector(self) -> PseudoUnderstandingDetector:
        return self._pseudo_understanding

    @property
    def insight_detector(self) -> InsightDetector:
        return self._insight_detector

    @property
    def reward_scheduler(self) -> VariableRewardScheduler:
        return self._reward_scheduler

    def add_events(self, events: list[RawEvent]) -> None:
        """Add events to the buffer for next fusion cycle."""
        self._event_buffer.extend(events)

    def run_cycle(self) -> MomentFlags:
        """
        Run one fusion cycle: process all buffered events through signal
        processors and moment detectors, producing moment flags.

        This is the heart of the system.
        """
        self._cycle_count += 1
        events = list(self._event_buffer)
        self._event_buffer.clear()

        # 1. Run all signal processors
        rt_result = self._response_time.process(events)
        rewind_result = self._rewind.process(events)
        idle_result = self._idle.process(events)
        variance_result = self._interaction_variance.process(events)
        scroll_result = self._scroll.process(events)
        pacing_result = self._session_pacing.process(events)

        # 2. Run moment detectors
        frustration_result = self._frustration_detector.detect(
            rewind_burst=rewind_result.rewind_burst_detected,
            response_time_trend=rt_result.response_time_trend,
            idle_trend=idle_result.recent_idle_trend,
        )

        # Record frustration for insight detection
        now_sec = time.time()
        self._insight_detector.record_frustration(now_sec, frustration_result.score)

        fatigue_result = self._fatigue_detector.detect(
            interaction_variance=variance_result.interaction_variance,
            session_duration_minutes=pacing_result.session_duration_minutes,
            idle_frequency=idle_result.idle_frequency,
            performance_decline=1.0 if pacing_result.performance_trajectory == "declining" else 0.0,
        )

        # Process question events for M14 and M08
        mastery_results = []
        insight_result = None
        for event in events:
            if isinstance(event, QuestionEvent):
                mastery = self._pseudo_understanding.check(event)
                mastery_results.append(mastery)

                # Check for insight
                if event.answer_correct:
                    insight_result = self._insight_detector.check_insight(event)
                    # Also record for reward scheduler
                    self._reward_scheduler.record_correct_answer(current_time=now_sec)

        # 3. Collect active moments and build interventions
        active_moments: list[str] = []
        interventions: list[InterventionRequest] = []

        # M07 — Frustration
        if frustration_result.level in ("warning", "critical"):
            active_moments.append(MOMENT_FRUSTRATION)
            if self._frustration_detector.should_intervene(frustration_result):
                urgency = URGENCY_IMMEDIATE if frustration_result.level == "critical" else URGENCY_NEXT_PAUSE
                intervention = InterventionRequest(
                    moment_id=MOMENT_FRUSTRATION,
                    intervention_type="rescue_intervention" if frustration_result.level == "critical" else "method_switch",
                    urgency=urgency,
                    payload={
                        "timestamp": now_sec,
                        "frustration_score": frustration_result.score,
                        "dominant_signal": frustration_result.dominant_signal,
                    },
                    confidence=frustration_result.confidence,
                    signals_triggered=[frustration_result.dominant_signal],
                )
                interventions.append(intervention)
                self._interventions_fired.append(intervention)

        # M10 — Fatigue
        if fatigue_result.level in ("tired", "critical"):
            active_moments.append(MOMENT_FATIGUE)
            if self._fatigue_detector.should_force_break(fatigue_result):
                intervention = InterventionRequest(
                    moment_id=MOMENT_FATIGUE,
                    intervention_type="force_break",
                    urgency=URGENCY_IMMEDIATE,
                    payload={
                        "timestamp": now_sec,
                        "fatigue_score": fatigue_result.score,
                        "session_minutes": fatigue_result.session_minutes_elapsed,
                    },
                    confidence=min(1.0, fatigue_result.score + 0.1),
                    signals_triggered=["interaction_variance", "session_duration"],
                )
                interventions.append(intervention)
                self._interventions_fired.append(intervention)

        # M14 — Pseudo-understanding
        for mastery in mastery_results:
            if mastery.flag in ("probe", "flag"):
                if MOMENT_PSEUDO_UNDERSTANDING not in active_moments:
                    active_moments.append(MOMENT_PSEUDO_UNDERSTANDING)
                intervention = InterventionRequest(
                    moment_id=MOMENT_PSEUDO_UNDERSTANDING,
                    intervention_type=mastery.recommended_action,
                    urgency=URGENCY_NEXT_PAUSE if mastery.flag == "probe" else URGENCY_IMMEDIATE,
                    payload={
                        "timestamp": now_sec,
                        "question_id": mastery.question_id,
                        "concept_id": mastery.concept_id,
                        "authenticity_score": mastery.authenticity_score,
                    },
                    confidence=1.0 - mastery.authenticity_score,
                    signals_triggered=["response_time", "confidence_score"],
                )
                interventions.append(intervention)
                self._interventions_fired.append(intervention)

        # M08 — Insight
        if insight_result is not None and insight_result.detected:
            active_moments.append(MOMENT_INSIGHT)
            intervention = InterventionRequest(
                moment_id=MOMENT_INSIGHT,
                intervention_type="chain_concept",
                urgency=URGENCY_IMMEDIATE,
                payload={
                    "timestamp": now_sec,
                    "window_open_until": insight_result.window_open_until,
                    "chain_count": insight_result.recommended_chain_concept_count,
                },
                confidence=insight_result.confidence,
                signals_triggered=["frustration_history", "resolution_speed"],
            )
            interventions.append(intervention)
            self._interventions_fired.append(intervention)

        # 4. Build signal scores dict
        all_scores: dict[str, float] = {
            "frustration_score": frustration_result.score,
            "fatigue_score": fatigue_result.score,
            "response_time_mean_ms": rt_result.mean_response_time_ms,
            "fast_answer_rate": rt_result.fast_answer_rate,
            "rewinds_per_minute": rewind_result.rewinds_per_minute,
            "idle_frequency": idle_result.idle_frequency,
            "interaction_variance": variance_result.interaction_variance,
            "fatigue_probability": variance_result.fatigue_probability,
            "mean_scroll_speed": scroll_result.mean_scroll_speed,
            "session_duration_minutes": pacing_result.session_duration_minutes,
            "engagement_rate": pacing_result.content_engagement_rate,
        }

        # 5. Determine priority intervention
        priority: Optional[InterventionRequest] = None
        if interventions:
            # Sort by urgency: immediate > next_pause > deferred
            urgency_order = {URGENCY_IMMEDIATE: 0, URGENCY_NEXT_PAUSE: 1, URGENCY_DEFERRED: 2}
            interventions.sort(key=lambda i: (urgency_order.get(i.urgency, 3), -i.confidence))
            priority = interventions[0]

        # 6. Persist snapshot to DB
        if self._signal_repo is not None:
            try:
                self._signal_repo.insert_snapshot(
                    session_id=self._session_id,
                    timestamp=now_sec * 1000,
                    response_time_mean_ms=rt_result.mean_response_time_ms,
                    response_time_trend=rt_result.response_time_trend,
                    fast_answer_rate=rt_result.fast_answer_rate,
                    rewinds_per_minute=rewind_result.rewinds_per_minute,
                    rewind_burst=rewind_result.rewind_burst_detected,
                    idle_frequency=idle_result.idle_frequency,
                    interaction_variance=variance_result.interaction_variance,
                    scroll_pattern=scroll_result.scroll_pattern,
                    frustration_score=frustration_result.score,
                    fatigue_score=fatigue_result.score,
                    active_moments=active_moments,
                )
            except Exception as e:
                logger.warning("Failed to persist signal snapshot: {}", e)

        flags = MomentFlags(
            session_id=self._session_id,
            timestamp=now_sec * 1000,
            active_moments=active_moments,
            interventions_ready=interventions,
            priority_intervention=priority,
            all_signal_scores=all_scores,
        )

        if active_moments:
            logger.info("Fusion cycle {}: active_moments={}, priority={}", 
                       self._cycle_count, active_moments, 
                       priority.moment_id if priority else "none")
        else:
            logger.debug("Fusion cycle {}: no active moments", self._cycle_count)

        return flags

    async def run_loop(
        self,
        event_queue: asyncio.Queue[RawEvent],
        interval_ms: Optional[int] = None,
    ) -> None:
        """
        Run the fusion engine in a continuous loop, consuming events from queue.

        This is used in production. For testing, call run_cycle() directly.
        """
        if interval_ms is None:
            interval_ms = int(get_threshold("FUSION_CYCLE_INTERVAL_MS"))

        self._running = True
        interval_sec = interval_ms / 1000.0
        logger.info("Fusion loop started (interval={}ms)", interval_ms)

        while self._running:
            # Drain all available events from queue
            while not event_queue.empty():
                try:
                    event = event_queue.get_nowait()
                    self._event_buffer.append(event)
                except asyncio.QueueEmpty:
                    break

            # Run fusion cycle if we have events
            if self._event_buffer:
                self.run_cycle()

            await asyncio.sleep(interval_sec)

    def stop(self) -> None:
        """Stop the fusion loop."""
        self._running = False
        logger.info("Fusion loop stopped after {} cycles", self._cycle_count)
