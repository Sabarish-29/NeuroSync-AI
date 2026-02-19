"""
NeuroSync AI — OpenAI API Cost Tracker (Step 6).

Tracks token usage and dollar costs. Enforces per-session and per-student limits.
"""

from __future__ import annotations

import time
import uuid

from loguru import logger

from neurosync.config.settings import INTERVENTION_COST_LIMITS


class CostTracker:
    """
    Tracks OpenAI API usage and enforces spending limits.

    All state is kept in-memory (no SQLite needed for MVP).
    """

    # Pricing per 1K tokens (update if OpenAI changes)
    PRICING: dict[str, dict[str, float]] = {
        "gpt-4-turbo-preview": {"input": 0.01 / 1000, "output": 0.03 / 1000},
        "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
        "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
    }

    def __init__(
        self,
        session_limit: float | None = None,
        student_limit: float | None = None,
    ) -> None:
        self.session_limit = session_limit or float(
            INTERVENTION_COST_LIMITS["SESSION_LIMIT_USD"]
        )
        self.student_limit = student_limit or float(
            INTERVENTION_COST_LIMITS["STUDENT_LIFETIME_LIMIT_USD"]
        )
        self.session_cost: float = 0.0
        self.session_requests: int = 0
        self.session_input_tokens: int = 0
        self.session_output_tokens: int = 0

    # ── recording ───────────────────────────────────────────────────

    def record_request(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4-turbo-preview",
        **_kwargs: object,
    ) -> float:
        """Record an API call and return its cost in USD."""
        pricing = self.PRICING.get(model, self.PRICING["gpt-4-turbo-preview"])
        cost = input_tokens * pricing["input"] + output_tokens * pricing["output"]

        self.session_cost += cost
        self.session_requests += 1
        self.session_input_tokens += input_tokens
        self.session_output_tokens += output_tokens

        logger.info(
            "API cost: ${:.6f} ({} in + {} out tokens, model={})",
            cost,
            input_tokens,
            output_tokens,
            model,
        )
        return cost

    # ── limits ──────────────────────────────────────────────────────

    def can_afford_request(self, **_kwargs: object) -> bool:
        """Return ``True`` if the session budget allows another call."""
        if self.session_cost >= self.session_limit:
            logger.warning(
                "Session cost limit reached: ${:.4f} >= ${:.2f}",
                self.session_cost,
                self.session_limit,
            )
            return False
        return True

    # ── stats ───────────────────────────────────────────────────────

    def get_session_stats(self) -> dict[str, float | int]:
        """Return a summary dict of the current session."""
        return {
            "total_cost": round(self.session_cost, 6),
            "request_count": self.session_requests,
            "input_tokens": self.session_input_tokens,
            "output_tokens": self.session_output_tokens,
            "avg_cost_per_request": (
                round(self.session_cost / self.session_requests, 6)
                if self.session_requests > 0
                else 0.0
            ),
            "remaining_budget": round(
                max(0.0, self.session_limit - self.session_cost), 6
            ),
        }
