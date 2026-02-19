"""
NeuroSync AI — Cooldown Tracker.

Prevents intervention spam by tracking per-moment cooldown windows.
"""

from __future__ import annotations

from loguru import logger

from neurosync.fusion.state import InterventionProposal


class CooldownTracker:
    """Track and enforce cooldown windows for moments."""

    def __init__(self) -> None:
        self.cooldowns: dict[str, float] = {}  # moment_id → expires_at

    def is_on_cooldown(self, moment_id: str, current_time: float) -> bool:
        """Return ``True`` if *moment_id* is still cooling down."""
        if moment_id not in self.cooldowns:
            return False
        return current_time < self.cooldowns[moment_id]

    def set_cooldown(
        self,
        moment_id: str,
        current_time: float,
        cooldown_seconds: int,
    ) -> None:
        self.cooldowns[moment_id] = current_time + cooldown_seconds

    def filter_interventions(
        self,
        interventions: list[InterventionProposal],
        current_time: float,
    ) -> list[InterventionProposal]:
        """Remove interventions whose moment is on cooldown."""
        filtered: list[InterventionProposal] = []

        for proposal in interventions:
            if self.is_on_cooldown(proposal.moment_id, current_time):
                remaining = self.cooldowns[proposal.moment_id] - current_time
                logger.debug(
                    "Skipping {} — cooldown {:.0f}s remaining",
                    proposal.moment_id,
                    remaining,
                )
            else:
                filtered.append(proposal)

        return filtered

    def update_from_fired(
        self, interventions: list[InterventionProposal],
    ) -> None:
        """Set cooldowns for interventions that actually fired."""
        for proposal in interventions:
            if proposal.cooldown_seconds > 0:
                self.set_cooldown(
                    proposal.moment_id,
                    proposal.timestamp,
                    proposal.cooldown_seconds,
                )
