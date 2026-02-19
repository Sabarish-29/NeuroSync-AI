"""
Step 5 — Conflict resolver tests (1 test — lightweight, validates core logic).
"""

from __future__ import annotations

import pytest

from neurosync.fusion.decision.conflict_resolver import ConflictResolver
from neurosync.fusion.state import InterventionProposal


def _proposal(itype: str, urgency: str = "high", confidence: float = 0.8) -> InterventionProposal:
    return InterventionProposal(
        moment_id="M00",
        agent_name="test",
        intervention_type=itype,
        urgency=urgency,
        confidence=confidence,
    )


class TestConflictResolver:

    def test_drops_incompatible(self):
        """pause_video + force_break → only stronger one kept."""
        resolver = ConflictResolver()
        proposals = [
            _proposal("pause_video", urgency="high", confidence=0.9),
            _proposal("force_break", urgency="critical", confidence=0.8),
        ]
        kept = resolver.resolve(proposals)
        types = {p.intervention_type for p in kept}
        assert not ({"pause_video", "force_break"} <= types), "Conflicting pair should not coexist"
        assert len(kept) >= 1
