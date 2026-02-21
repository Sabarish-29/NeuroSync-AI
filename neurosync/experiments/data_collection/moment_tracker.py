"""
Moment Tracker — tracks which of the 22 moments fired during sessions.

Provides counts, timelines, and coverage analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from neurosync.core.constants import ALL_MOMENTS


@dataclass
class MomentEvent:
    """A single moment firing event."""

    moment_id: str
    timestamp: float
    confidence: float = 0.0


class MomentTracker:
    """Tracks moment firings across sessions."""

    def __init__(self, db_manager: Any = None):
        self.db = db_manager
        self._in_memory: dict[str, list[MomentEvent]] = {}

    def record_moment(
        self,
        session_id: str,
        moment_id: str,
        timestamp: float,
        confidence: float = 0.0,
    ) -> None:
        """Record a moment firing."""
        if session_id not in self._in_memory:
            self._in_memory[session_id] = []
        self._in_memory[session_id].append(
            MomentEvent(
                moment_id=moment_id,
                timestamp=timestamp,
                confidence=confidence,
            )
        )

    def get_moment_counts(self, session_id: str) -> dict[str, int]:
        """
        Count how many times each moment fired.

        Returns: {"M01": 3, "M07": 1, ...} with zeros for unfired moments.
        """
        events = self._in_memory.get(session_id, [])
        counts: dict[str, int] = {}
        for e in events:
            counts[e.moment_id] = counts.get(e.moment_id, 0) + 1

        # Fill zeros
        for m in ALL_MOMENTS:
            counts.setdefault(m, 0)

        return counts

    def get_moment_timeline(self, session_id: str) -> list[MomentEvent]:
        """Get chronological list of moment firings."""
        events = self._in_memory.get(session_id, [])
        return sorted(events, key=lambda e: e.timestamp)

    def get_coverage(self, session_id: str) -> float:
        """What fraction of the 22 moments fired at least once?"""
        counts = self.get_moment_counts(session_id)
        fired = sum(1 for c in counts.values() if c > 0)
        return fired / len(ALL_MOMENTS) if ALL_MOMENTS else 0.0

    def get_total_firings(self, session_id: str) -> int:
        """Total number of moment firings in a session."""
        return len(self._in_memory.get(session_id, []))

    def get_all_sessions(self) -> list[str]:
        """List of session IDs with recorded moments."""
        return list(self._in_memory.keys())
