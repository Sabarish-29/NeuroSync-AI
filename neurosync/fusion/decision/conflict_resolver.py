"""
NeuroSync AI — Conflict Resolver.

Ensures mutually-exclusive interventions are never fired together
and applies domain-specific compatibility logic.
"""

from __future__ import annotations

from neurosync.fusion.state import InterventionProposal


# ── conflict rules ──────────────────────────────────────────────────

INCOMPATIBLE_PAIRS: set[frozenset[str]] = {
    frozenset({"pause_video", "force_break"}),
    frozenset({"pause_video", "skip_to_challenge"}),
    frozenset({"force_break", "checkpoint_concepts"}),
    frozenset({"skip_to_challenge", "explain_concept"}),
}


class ConflictResolver:
    """Drop conflicting proposals — keep the higher-confidence one."""

    URGENCY_RANK: dict[str, int] = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    def resolve(
        self, proposals: list[InterventionProposal],
    ) -> list[InterventionProposal]:
        """Return a list free of mutually-exclusive conflicts."""
        if len(proposals) < 2:
            return list(proposals)

        # Sort best-first so we greedily keep the strongest
        ranked = sorted(
            proposals,
            key=lambda p: (self.URGENCY_RANK.get(p.urgency, 0), p.confidence),
            reverse=True,
        )

        kept: list[InterventionProposal] = []
        kept_types: set[str] = set()

        for proposal in ranked:
            if self._conflicts_with(proposal.intervention_type, kept_types):
                continue
            kept.append(proposal)
            kept_types.add(proposal.intervention_type)

        return kept

    @staticmethod
    def _conflicts_with(itype: str, existing: set[str]) -> bool:
        for ex in existing:
            if frozenset({itype, ex}) in INCOMPATIBLE_PAIRS:
                return True
        return False
