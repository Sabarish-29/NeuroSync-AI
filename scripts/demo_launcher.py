#!/usr/bin/env python3
"""
CLI: Launch demo mode.

Usage:
    python scripts/demo_launcher.py --mode scripted
    python scripts/demo_launcher.py --mode live --duration 3
"""

from __future__ import annotations

import argparse
import asyncio

from loguru import logger


async def main(mode: str, duration: int, realtime: bool) -> None:
    if mode == "scripted":
        from neurosync.experiments.demo_modes.scripted_demo import ScriptedDemo

        demo = ScriptedDemo(realtime=realtime)
        print("=" * 60)
        print("  NeuroSync AI — Scripted Demo (5 minutes)")
        print("=" * 60)
        result = await demo.run()
        print(f"\nDemo complete!")
        print(f"  Steps executed: {result.steps_executed}")
        print(f"  Moments demonstrated: {', '.join(result.moments_demonstrated)}")
        print(f"  Duration: {result.duration_seconds:.1f}s")
        print(f"  Success: {result.success}")

    elif mode == "live":
        from neurosync.experiments.demo_modes.live_demo import LiveDemo

        demo = LiveDemo(duration_minutes=duration, realtime=realtime)
        print("=" * 60)
        print(f"  NeuroSync AI — Live Demo ({duration} minutes)")
        print("=" * 60)
        result = await demo.run()
        print(f"\nLive demo complete!")
        print(f"  Session: {result.session_id}")
        print(f"  Cycles run: {result.cycles_run}")
        print(f"  Moments fired: {result.moments_fired}")
        print(f"  Total interventions: {result.interventions_total}")
        print(f"  Duration: {result.duration_seconds:.1f}s")

    else:
        print(f"Unknown mode: {mode}. Use 'scripted' or 'live'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch NeuroSync demo")
    parser.add_argument(
        "--mode",
        choices=["scripted", "live"],
        default="scripted",
        help="Demo mode",
    )
    parser.add_argument(
        "--duration", type=int, default=5, help="Duration in minutes (live mode)"
    )
    parser.add_argument(
        "--realtime", action="store_true", help="Run in real-time (with delays)"
    )
    args = parser.parse_args()

    asyncio.run(main(args.mode, args.duration, args.realtime))
