#!/usr/bin/env python
"""
NeuroSync AI — Intervention Engine Demo (Step 6).

Generates all 6 intervention types. Uses the real OpenAI API if
OPENAI_API_KEY is set, otherwise falls back to templates.

Usage:
    python scripts/demo_interventions.py
"""

from __future__ import annotations

import asyncio
import os
import time

from loguru import logger

from neurosync.interventions.generator import InterventionGenerator


DEMO_SCENARIOS = [
    {
        "label": "SIMPLIFY (M02)",
        "type": "simplify",
        "context": {
            "original_phrase": "The mitochondrial electron transport chain phosphorylates ADP",
            "surrounding_sentence": "The mitochondrial electron transport chain phosphorylates ADP into ATP.",
            "subject": "biology",
            "grade_level": 8,
            "complexity_score": 16.2,
        },
    },
    {
        "label": "EXPLAIN (M03)",
        "type": "explain",
        "context": {
            "concept_name": "East India Company",
            "lesson_topic": "British colonialism",
            "grade_level": 10,
            "missing_prerequisites": ["mercantilism"],
        },
    },
    {
        "label": "MISCONCEPTION (M15)",
        "type": "misconception",
        "context": {
            "concept_name": "photosynthesis",
            "wrong_answer": "plants get food from soil",
            "correct_answer": "plants make food from sunlight",
            "grade_level": 8,
        },
    },
    {
        "label": "RESCUE (M07)",
        "type": "rescue",
        "context": {
            "concept_name": "quadratic equations",
            "frustration_score": 0.78,
            "failed_attempts": 4,
            "lesson_topic": "algebra",
            "grade_level": 9,
        },
    },
    {
        "label": "PLATEAU (M22)",
        "type": "plateau",
        "context": {
            "concept_name": "osmosis",
            "concept_definition": "Movement of water through a semipermeable membrane from low to high solute concentration.",
            "failed_methods": ["video", "diagram"],
            "new_method": "story_analogy",
            "grade_level": 8,
        },
    },
    {
        "label": "APPLICATION (M18)",
        "type": "application",
        "context": {
            "concept_name": "photosynthesis",
            "concept_definition": "The process by which plants convert light energy into chemical energy (glucose).",
            "grade_level": 8,
            "subject": "biology",
        },
    },
]


async def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY", "")
    mode = "GPT-4" if api_key.startswith("sk-") else "FALLBACK (no API key)"
    print(f"\n{'=' * 60}")
    print(f"  NEUROSYNC AI — Intervention Engine Demo")
    print(f"  Mode: {mode}")
    print(f"{'=' * 60}\n")

    gen = InterventionGenerator(api_key=api_key or "sk-test-dummy")
    total_tokens = 0
    total_cost = 0.0

    for i, scenario in enumerate(DEMO_SCENARIOS, 1):
        t0 = time.time()
        result = await gen.generate(scenario["type"], scenario["context"])
        elapsed = time.time() - t0

        total_tokens += result.tokens_used
        cost = gen.cost_tracker.session_cost

        print(f"[{i}/6] {scenario['label']}")
        print(f"  Model: {result.model}")
        print(f"  Output:\n    {result.content[:300]}")
        print(f"  Tokens: {result.tokens_used}  Cost: ${cost:.4f}  Time: {elapsed:.2f}s")
        print()

    stats = gen.cost_tracker.get_session_stats()
    print(f"{'=' * 60}")
    print(f"  SUMMARY")
    print(f"  Total interventions: 6")
    print(f"  Total cost: ${stats['total_cost']:.4f}")
    print(f"  Total requests: {stats['request_count']}")
    print(f"  Remaining budget: ${stats['remaining_budget']:.2f}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())
