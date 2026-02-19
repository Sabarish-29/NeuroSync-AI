"""
Step 5 — Prioritiser tests (4 tests).
"""

from __future__ import annotations

import pytest

from neurosync.fusion.decision.prioritizer import InterventionPrioritizer
from neurosync.fusion.state import InterventionProposal


def _proposal(
    moment_id: str = "M01",
    itype: str = "pause_video",
    urgency: str = "medium",
    confidence: float = 0.7,
    agent: str = "test",
) -> InterventionProposal:
    return InterventionProposal(
        moment_id=moment_id,
        agent_name=agent,
        intervention_type=itype,
        urgency=urgency,
        confidence=confidence,
    )


class TestPrioritizer:

    def test_critical_urgency_always_first(self):
        """Critical proposals are selected before high/medium."""
        p = InterventionPrioritizer()
        proposals = [
            _proposal(urgency="medium", confidence=0.9, moment_id="M02"),
            _proposal(urgency="critical", confidence=0.6, moment_id="M07"),
            _proposal(urgency="high", confidence=0.8, moment_id="M03"),
        ]
        selected = p.prioritize(proposals)
        assert selected[0].moment_id == "M07"

    def test_max_2_interventions(self):
        """At most 2 interventions per cycle."""
        p = InterventionPrioritizer()
        proposals = [
            _proposal(moment_id="M01", urgency="high"),
            _proposal(moment_id="M02", urgency="high", itype="simplify_phrase"),
            _proposal(moment_id="M03", urgency="high", itype="explain_concept"),
            _proposal(moment_id="M10", urgency="high", itype="force_break"),
            _proposal(moment_id="M15", urgency="high", itype="clear_misconception"),
        ]
        selected = p.prioritize(proposals, max_interventions=2)
        assert len(selected) == 2

    def test_removes_conflicting(self):
        """pause_video + force_break conflict → only one selected."""
        p = InterventionPrioritizer()
        proposals = [
            _proposal(moment_id="M01", itype="pause_video", urgency="high"),
            _proposal(moment_id="M10", itype="force_break", urgency="high"),
        ]
        selected = p.prioritize(proposals)
        # One should be dropped due to conflict
        assert len(selected) == 1

    def test_one_per_moment(self):
        """Two proposals for same moment → only one fires."""
        p = InterventionPrioritizer()
        proposals = [
            _proposal(moment_id="M03", itype="explain_concept", confidence=0.8),
            _proposal(moment_id="M03", itype="explain_concept", confidence=0.6),
        ]
        selected = p.prioritize(proposals)
        assert len(selected) == 1
