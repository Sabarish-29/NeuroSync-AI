"""
NeuroSync AI — Fallback Templates for intervention content.

Used when GPT-4 is unavailable, rate-limited, or cost-capped.
These are simple, rule-based alternatives — better than nothing.
"""

from __future__ import annotations

import re


class FallbackTemplates:
    """Template-based fallback generator for all intervention types."""

    # Basic word-level simplification table
    _SIMPLIFY_MAP: dict[str, str] = {
        "utilize": "use",
        "commence": "start",
        "terminate": "end",
        "approximately": "about",
        "numerous": "many",
        "substantial": "large",
        "facilitate": "help",
        "obtain": "get",
        "possess": "have",
        "demonstrate": "show",
        "indicates": "shows",
        "sufficient": "enough",
        "regarding": "about",
        "therefore": "so",
        "however": "but",
    }

    def generate(self, intervention_type: str, context: dict) -> str | list[str]:
        """Dispatch to the correct template method."""
        handler = {
            "simplify": self._simplify,
            "explain": self._explain,
            "misconception": self._misconception,
            "rescue": self._rescue,
            "plateau": self._plateau,
            "application": self._application,
        }.get(intervention_type, self._generic)
        return handler(context)

    # ── templates ───────────────────────────────────────────────────

    def _simplify(self, ctx: dict) -> str:
        phrase = ctx.get("original_phrase", "")
        result = phrase
        for cplx, simple in self._SIMPLIFY_MAP.items():
            result = re.sub(rf"\b{cplx}\b", simple, result, flags=re.IGNORECASE)
        return result

    def _explain(self, ctx: dict) -> str:
        concept = ctx.get("concept_name", "this concept")
        return (
            f"{concept} is an important concept in this topic. "
            "Let's break it down step by step to understand what it means."
        )

    def _misconception(self, ctx: dict) -> str:
        concept = ctx.get("concept_name", "this")
        return (
            f"There's a common misunderstanding about {concept}. "
            "Let's clarify what it actually means."
        )

    def _rescue(self, ctx: dict) -> str:
        return (
            "This is challenging material, and that's completely normal. "
            "Let me try explaining it in a different way."
        )

    def _plateau(self, ctx: dict) -> str:
        return (
            "Sometimes a concept clicks when we approach it differently. "
            "Let's try a new perspective."
        )

    def _application(self, ctx: dict) -> list[str]:
        concept = ctx.get("concept_name", "this concept")
        return [
            f"How would you use {concept} in a real situation?",
            f"Can you think of an example of {concept} in everyday life?",
            f"What would happen if {concept} didn't exist?",
        ]

    def _generic(self, _ctx: dict) -> str:
        return "Let's review this concept together."
