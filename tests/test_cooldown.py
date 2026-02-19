"""
Step 5 — Cooldown tracker tests (3 tests).
"""

from __future__ import annotations

import time

import pytest

from neurosync.fusion.decision.cooldown import CooldownTracker
from neurosync.fusion.state import InterventionProposal


def _proposal(moment_id: str, cooldown: int = 120, ts: float = 0) -> InterventionProposal:
    return InterventionProposal(
        moment_id=moment_id,
        agent_name="test",
        intervention_type="test_type",
        cooldown_seconds=cooldown,
        timestamp=ts or time.time(),
    )


class TestCooldownTracker:

    def test_blocks_recent(self):
        """M01 fired 60 s ago with 120 s cooldown → blocked."""
        tracker = CooldownTracker()
        now = time.time()
        tracker.set_cooldown("M01", now - 60, 120)
        assert tracker.is_on_cooldown("M01", now) is True

    def test_allows_after_expiry(self):
        """M01 fired 130 s ago with 120 s cooldown → allowed."""
        tracker = CooldownTracker()
        now = time.time()
        tracker.set_cooldown("M01", now - 130, 120)
        assert tracker.is_on_cooldown("M01", now) is False

    def test_independent_per_moment(self):
        """M01 on cooldown, M02 not → M02 allowed."""
        tracker = CooldownTracker()
        now = time.time()
        tracker.set_cooldown("M01", now - 60, 120)
        assert tracker.is_on_cooldown("M01", now) is True
        assert tracker.is_on_cooldown("M02", now) is False
