"""
NeuroSync AI — Full session simulation script.

Simulates a realistic 30-minute student session with:
  - 200 events (mix of all types)
  - A frustration spike at minute 8 (many rewinds, slow answers)
  - A fatigue onset at minute 22 (erratic interaction variance)
  - 3 fast suspicious answers (M14 flags) scattered through
  - 1 insight moment at minute 15 (struggle → fast correct answer)

Usage:
    python scripts/simulate_session.py
"""

import random
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neurosync.behavioral.fusion import BehavioralFusionEngine
from neurosync.config.settings import DATABASE_PATH
from neurosync.core.events import (
    IdleEvent,
    QuestionEvent,
    RawEvent,
    SessionConfig,
    VideoEvent,
)
from neurosync.database.manager import DatabaseManager


def _ts(base: float, minute: float, offset_sec: float = 0.0) -> float:
    """Create a timestamp at a specific minute + offset in the session."""
    return base + (minute * 60 + offset_sec) * 1000


def simulate() -> None:
    print("=" * 60)
    print("  NeuroSync AI — Session Simulation")
    print("=" * 60)
    print()

    # Init DB
    db = DatabaseManager(DATABASE_PATH)
    db.initialise()

    # Session config
    session_start = time.time() * 1000
    config = SessionConfig(
        student_id="sim_student_001",
        lesson_id="physics_chapter_3",
        started_at=session_start,
    )

    fusion = BehavioralFusionEngine(
        session_id=config.session_id,
        session_start_ms=session_start,
        db_manager=db,
    )

    print(f"Session ID: {config.session_id}")
    print(f"Student: {config.student_id}")
    print(f"Lesson: {config.lesson_id}")
    print(f"Simulating 30-minute session with 200 events...")
    print()

    events: list[RawEvent] = []

    # =========================================================================
    # Phase 1: Normal engagement (minutes 0-7)
    # =========================================================================
    print("Phase 1: Normal engagement (0-7 min)")
    for i in range(50):
        minute = random.uniform(0, 7)
        event_type = random.choice(["click", "scroll", "video_play", "video_pause"])
        event = RawEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, minute, random.uniform(0, 30)),
            event_type=event_type,
            metadata={"scroll_y": random.uniform(0, 500)} if event_type == "scroll" else {},
        )
        events.append(event)

    # Normal questions (reasonable response times)
    for i in range(8):
        minute = random.uniform(1, 7)
        event = QuestionEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, minute, random.uniform(0, 30)),
            event_type="answer_submitted",
            question_id=f"q_normal_{i}",
            concept_id=f"concept_{random.randint(1, 10)}",
            answer_correct=random.random() > 0.3,
            response_time_ms=random.uniform(5000, 12000),
            confidence_score=random.randint(3, 5),
        )
        events.append(event)

    # =========================================================================
    # Phase 2: FRUSTRATION SPIKE (minutes 7-10)
    # =========================================================================
    print("Phase 2: Frustration spike (7-10 min)")

    # Many rewinds in quick succession (burst)
    for i in range(6):
        event = VideoEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, 8, i * 8),  # 6 rewinds in ~48 seconds
            event_type="video_rewind",
            video_id="vid_physics_3",
            playback_position_ms=120000 + random.uniform(-5000, 5000),
        )
        events.append(event)

    # Slow, frustrated answers
    for i in range(5):
        event = QuestionEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, 8.5, i * 15),
            event_type="answer_submitted",
            question_id=f"q_frustrated_{i}",
            concept_id="concept_3",
            answer_correct=random.random() > 0.7,  # mostly wrong
            response_time_ms=random.uniform(15000, 25000),  # very slow
            confidence_score=random.randint(1, 2),
        )
        events.append(event)

    # Increasing idle periods during frustration
    for i in range(4):
        event = IdleEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, 9, i * 20),
            event_type="mouse_idle",
            idle_duration_ms=random.uniform(8000, 15000),
            preceding_event_type="click",
        )
        events.append(event)

    # M14: First suspicious fast answer at minute 9
    events.append(QuestionEvent(
        session_id=config.session_id,
        student_id=config.student_id,
        timestamp=_ts(session_start, 9, 30),
        event_type="answer_submitted",
        question_id="q_suspicious_1",
        concept_id="concept_5",
        answer_correct=True,
        response_time_ms=1800,  # suspiciously fast
        confidence_score=2,
    ))

    # =========================================================================
    # Phase 3: Recovery + Insight (minutes 10-17)
    # =========================================================================
    print("Phase 3: Recovery + Insight at minute 15")

    # Some normal activity
    for i in range(25):
        minute = random.uniform(10, 14)
        event = RawEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, minute, random.uniform(0, 30)),
            event_type=random.choice(["click", "scroll", "video_play"]),
            metadata={"scroll_y": random.uniform(0, 500)},
        )
        events.append(event)

    # Struggle period before insight (frustration markers at 14-15)
    for i in range(4):
        event = VideoEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, 14, i * 15),
            event_type="video_rewind",
            video_id="vid_physics_3",
            playback_position_ms=200000 + random.uniform(-3000, 3000),
        )
        events.append(event)

    # INSIGHT: Fast correct answer after struggle
    events.append(QuestionEvent(
        session_id=config.session_id,
        student_id=config.student_id,
        timestamp=_ts(session_start, 15, 7),
        event_type="answer_submitted",
        question_id="q_insight",
        concept_id="concept_3",  # same concept that was frustrating
        answer_correct=True,
        response_time_ms=2800,  # fast and correct
        confidence_score=5,
    ))

    # Energy surge after insight (fast interactions)
    for i in range(5):
        event = RawEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, 15, 10 + i * 3),
            event_type="click",
        )
        events.append(event)

    # M14: Second suspicious answer at minute 16
    events.append(QuestionEvent(
        session_id=config.session_id,
        student_id=config.student_id,
        timestamp=_ts(session_start, 16, 20),
        event_type="answer_submitted",
        question_id="q_suspicious_2",
        concept_id="concept_7",
        answer_correct=True,
        response_time_ms=2200,
        confidence_score=1,
    ))

    # Normal questions
    for i in range(6):
        event = QuestionEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, random.uniform(15, 17), random.uniform(0, 30)),
            event_type="answer_submitted",
            question_id=f"q_recovery_{i}",
            concept_id=f"concept_{random.randint(1, 10)}",
            answer_correct=random.random() > 0.2,
            response_time_ms=random.uniform(6000, 10000),
            confidence_score=random.randint(3, 5),
        )
        events.append(event)

    # =========================================================================
    # Phase 4: FATIGUE ONSET (minutes 18-30)
    # =========================================================================
    print("Phase 4: Fatigue onset (18-30 min)")

    # Erratic interaction patterns (hallmark of fatigue)
    for i in range(50):
        minute = random.uniform(18, 30)
        # Erratic timing: sometimes very fast, sometimes very slow
        if random.random() > 0.5:
            offset = random.uniform(0, 2)  # fast
        else:
            offset = random.uniform(8, 20)  # slow
        event = RawEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, minute, offset),
            event_type=random.choice(["click", "scroll", "mouse_active"]),
            metadata={"scroll_y": random.uniform(0, 1000)} if random.random() > 0.5 else {},
        )
        events.append(event)

    # Increasing idle periods
    for i in range(8):
        minute = random.uniform(20, 28)
        event = IdleEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, minute, random.uniform(0, 30)),
            event_type="mouse_idle",
            idle_duration_ms=random.uniform(5000, 20000),
            preceding_event_type="click",
        )
        events.append(event)

    # Slower, more inconsistent answers
    for i in range(8):
        minute = random.uniform(20, 28)
        event = QuestionEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, minute, random.uniform(0, 30)),
            event_type="answer_submitted",
            question_id=f"q_fatigue_{i}",
            concept_id=f"concept_{random.randint(1, 10)}",
            answer_correct=random.random() > 0.4,
            response_time_ms=random.uniform(3000, 20000),  # very inconsistent
            confidence_score=random.randint(2, 4),
        )
        events.append(event)

    # M14: Third suspicious answer at minute 25
    events.append(QuestionEvent(
        session_id=config.session_id,
        student_id=config.student_id,
        timestamp=_ts(session_start, 25, 15),
        event_type="answer_submitted",
        question_id="q_suspicious_3",
        concept_id="concept_9",
        answer_correct=True,
        response_time_ms=1500,
        confidence_score=2,
    ))

    # Some rewinds in fatigue phase
    for i in range(3):
        event = VideoEvent(
            session_id=config.session_id,
            student_id=config.student_id,
            timestamp=_ts(session_start, random.uniform(22, 27), random.uniform(0, 30)),
            event_type="video_rewind",
            video_id="vid_physics_3",
            playback_position_ms=random.uniform(200000, 400000),
        )
        events.append(event)

    # Sort all events by timestamp
    events.sort(key=lambda e: e.timestamp)

    print(f"\nTotal events generated: {len(events)}")
    print()

    # =========================================================================
    # Run fusion engine
    # =========================================================================
    print("-" * 60)
    print("Running fusion engine...")
    print("-" * 60)
    print()

    # Track detections
    frustration_warnings = 0
    frustration_criticals = 0
    fatigue_warnings = 0
    fatigue_mandatories = 0
    pseudo_flags = 0
    insight_detections = 0
    interventions_log: list[tuple[float, str, str, float]] = []

    # Process events in batches (simulating real-time)
    batch_size = 5
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        fusion.add_events(batch)
        flags = fusion.run_cycle()

        # Track what was detected
        sim_minute = (batch[-1].timestamp - session_start) / 60000

        for moment in flags.active_moments:
            if moment == "M07":
                frustration_warnings += 1
            if moment == "M10":
                fatigue_warnings += 1
            if moment == "M14":
                pseudo_flags += 1
            if moment == "M08":
                insight_detections += 1

        for intervention in flags.interventions_ready:
            sim_time = f"{int(sim_minute):02d}:{int((sim_minute % 1) * 60):02d}"
            interventions_log.append((
                sim_minute,
                intervention.moment_id,
                intervention.intervention_type,
                intervention.confidence,
            ))

            if intervention.moment_id == "M07" and intervention.intervention_type == "rescue_intervention":
                frustration_criticals += 1
            if intervention.moment_id == "M10" and intervention.intervention_type == "force_break":
                fatigue_mandatories += 1

        # Progress indicator
        if (i // batch_size) % 8 == 0:
            score_str = ""
            if flags.all_signal_scores:
                f_score = flags.all_signal_scores.get("frustration_score", 0)
                t_score = flags.all_signal_scores.get("fatigue_score", 0)
                score_str = f" | frustration={f_score:.2f}, fatigue={t_score:.2f}"
            print(f"  [{sim_minute:5.1f} min] {len(batch)} events processed"
                  f"{score_str}"
                  f"{' → ' + ', '.join(flags.active_moments) if flags.active_moments else ''}")

    # =========================================================================
    # Final report
    # =========================================================================
    print()
    print("=" * 60)
    print("  SESSION SIMULATION COMPLETE")
    print("=" * 60)
    print(f"  Duration: 30 minutes (simulated)")
    print(f"  Total events: {len(events)}")
    print()
    print("  Moments detected:")
    print(f"    M07 (Frustration): {frustration_warnings} warning cycles, "
          f"{frustration_criticals} critical intervention(s)")
    print(f"    M10 (Fatigue): {fatigue_warnings} warning cycles, "
          f"{fatigue_mandatories} mandatory break(s)")
    print(f"    M14 (Pseudo-mastery): {pseudo_flags} flag(s) raised")
    print(f"    M08 (Insight): {insight_detections} detected")
    print()

    if interventions_log:
        print("  Interventions that would have fired:")
        for minute, moment, itype, conf in interventions_log:
            sim_time = f"{int(minute):02d}:{int((minute % 1) * 60):02d}"
            print(f"    [{sim_time}] {moment} → {itype} (confidence: {conf:.2f})")
    print()

    # Verification
    all_ok = True
    checks = [
        ("Database wrote events", len(events) > 0, f"{len(events)} events"),
        ("Frustration detected", frustration_warnings > 0 or frustration_criticals > 0, 
         f"{frustration_warnings} warnings, {frustration_criticals} critical"),
        ("Pseudo-mastery flagged", pseudo_flags > 0, f"{pseudo_flags} flags"),
        ("Signal processing ran", fusion._cycle_count > 0, f"{fusion._cycle_count} cycles"),
    ]

    for check_name, passed, detail in checks:
        status = "✓" if passed else "✗"
        if not passed:
            all_ok = False
        print(f"  {status} {check_name}: {detail}")

    print()
    if all_ok:
        print("  All detectors verified ✓")
    else:
        print("  Some checks failed — review output above")

    db.close()


if __name__ == "__main__":
    simulate()
