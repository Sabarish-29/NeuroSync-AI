"""
NeuroSync AI — Interactive CLI demo to verify event collection works.

Runs a quick interactive session where you can type events and see
signal processing in real time.

Usage:
    python scripts/demo_collector.py
"""

import asyncio
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neurosync.behavioral.collector import AsyncEventCollector
from neurosync.behavioral.fusion import BehavioralFusionEngine
from neurosync.config.settings import DATABASE_PATH
from neurosync.core.events import (
    QuestionEvent,
    RawEvent,
    SessionConfig,
    VideoEvent,
)
from neurosync.database.manager import DatabaseManager


async def main() -> None:
    print("=" * 60)
    print("  NeuroSync AI — Interactive Demo")
    print("=" * 60)
    print()

    # Init DB
    db = DatabaseManager(DATABASE_PATH)
    db.initialise()

    # Create session
    config = SessionConfig(student_id="demo_student", lesson_id="demo_lesson")
    collector = AsyncEventCollector(config, db)
    await collector.start()

    fusion = BehavioralFusionEngine(
        session_id=config.session_id,
        session_start_ms=config.started_at,
        db_manager=db,
    )

    print(f"Session started: {config.session_id}")
    print()
    print("Commands:")
    print("  click     — Record a click event")
    print("  question  — Record a question answer")
    print("  rewind    — Record a video rewind")
    print("  idle      — Record an idle period")
    print("  status    — Show current signal scores")
    print("  quit      — End session")
    print()

    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd == "quit":
            break
        elif cmd == "click":
            event = RawEvent(
                session_id=config.session_id,
                student_id=config.student_id,
                event_type="click",
            )
            await collector.record_event(event)
            fusion.add_events([event])
            print("  Click recorded")
        elif cmd == "question":
            event = QuestionEvent(
                session_id=config.session_id,
                student_id=config.student_id,
                event_type="answer_submitted",
                question_id=str(uuid.uuid4())[:8],
                concept_id="demo_concept",
                answer_correct=True,
                response_time_ms=2500.0,
                confidence_score=3,
            )
            await collector.record_question(event)
            fusion.add_events([event])
            print(f"  Question recorded (rt={event.response_time_ms}ms)")
        elif cmd == "rewind":
            event = VideoEvent(
                session_id=config.session_id,
                student_id=config.student_id,
                event_type="video_rewind",
                video_id="demo_video",
                playback_position_ms=float(time.time() * 1000 % 300000),
            )
            await collector.record_video(event)
            fusion.add_events([event])
            print("  Rewind recorded")
        elif cmd == "idle":
            from neurosync.core.events import IdleEvent
            event = IdleEvent(
                session_id=config.session_id,
                student_id=config.student_id,
                event_type="mouse_idle",
                idle_duration_ms=5000.0,
                preceding_event_type="click",
            )
            await collector.record_idle(event)
            fusion.add_events([event])
            print("  Idle recorded")
        elif cmd == "status":
            flags = fusion.run_cycle()
            summary = await collector.get_session_summary()
            print(f"\n  Session: {summary['total_events']} events, "
                  f"{summary['duration_minutes']:.1f} min")
            print(f"  Scores: {flags.all_signal_scores}")
            print(f"  Active moments: {flags.active_moments or 'none'}")
            if flags.priority_intervention:
                print(f"  Priority: {flags.priority_intervention.moment_id} "
                      f"({flags.priority_intervention.intervention_type})")
            print()
        else:
            print("  Unknown command. Use: click, question, rewind, idle, status, quit")

    await collector.close()
    db.close()
    print("\nSession ended. Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
