"""
NeuroSync AI — Intervention Prioritiser.

Ranks and selects which interventions actually fire each cycle.

Rules:
    1. CRITICAL urgency always fires
    2. HIGH fires unless conflicting with critical
    3. Max 2 interventions per cycle (avoid overwhelming student)
    4. Only 1 intervention per moment per cycle
    5. Mutually-exclusive types are blocked
"""

from __future__ import annotations

from neurosync.fusion.state import InterventionProposal


class InterventionPrioritizer:
    """Select the top interventions to fire this cycle."""

    URGENCY_PRIORITY: dict[str, int] = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    # Mutually exclusive intervention types
    CONFLICTS: dict[str, list[str]] = {
        "pause_video": ["force_break", "skip_to_challenge"],
        "force_break": ["pause_video", "checkpoint_concepts"],
        "skip_to_challenge": ["pause_video", "explain_concept"],
    }

    def prioritize(
        self,
        interventions: list[InterventionProposal],
        max_interventions: int = 2,
    ) -> list[InterventionProposal]:
        """Return the top interventions that should fire."""
        if not interventions:
            return []

        # Sort by urgency then confidence (highest first)
        ranked = sorted(
            interventions,
            key=lambda i: (
                self.URGENCY_PRIORITY.get(i.urgency, 0),
                i.confidence,
            ),
            reverse=True,
        )

        selected: list[InterventionProposal] = []

        for proposal in ranked:
            if len(selected) >= max_interventions:
                break
            if self._has_conflict(proposal, selected):
                continue
            # One intervention per moment
            if any(s.moment_id == proposal.moment_id for s in selected):
                continue
            selected.append(proposal)

        return selected

    # ── internal ────────────────────────────────────────────────────

    def _has_conflict(
        self,
        proposal: InterventionProposal,
        selected: list[InterventionProposal],
    ) -> bool:
        conflicts = self.CONFLICTS.get(proposal.intervention_type, [])
        return any(s.intervention_type in conflicts for s in selected)
