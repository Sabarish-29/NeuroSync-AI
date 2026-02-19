"""
NeuroSync AI — Intervention Coordinator (Step 6).

High-level coordinator that accepts an InterventionRequest (from Step 5)
and returns generated content ready to display to the student.
"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger

from neurosync.core.events import InterventionRequest
from neurosync.interventions.generator import GeneratedContent, InterventionGenerator


# Mapping from InterventionRequest.intervention_type → generator type key
_REQUEST_TYPE_MAP: dict[str, str] = {
    "simplify_phrase": "simplify",
    "explain_concept": "explain",
    "clear_misconception": "misconception",
    "rescue_frustration": "rescue",
    "rescue_intervention": "rescue",
    "method_switch": "rescue",
    "method_overhaul": "plateau",
    "plateau_escape": "plateau",
    "application_test": "application",
    "chain_concept": "explain",
}


class InterventionCoordinator:
    """
    Accepts ``InterventionRequest`` objects produced by the fusion engine
    and returns ``GeneratedContent`` ready for the student.
    """

    def __init__(self, generator: InterventionGenerator) -> None:
        self._generator = generator

    async def handle(
        self,
        request: InterventionRequest,
        extra_context: dict[str, Any] | None = None,
    ) -> GeneratedContent:
        """
        Handle an intervention request end-to-end.

        Parameters
        ----------
        request
            The ``InterventionRequest`` from the fusion engine.
        extra_context
            Optional additional context (concept name, lesson topic, etc.).
        """
        gen_type = _REQUEST_TYPE_MAP.get(request.intervention_type, "explain")
        context: dict[str, Any] = {**request.payload, **(extra_context or {})}
        priority = "critical" if request.urgency == "immediate" else "normal"

        logger.info(
            "Coordinator handling {} (moment={}, urgency={})",
            gen_type,
            request.moment_id,
            request.urgency,
        )

        return await self._generator.generate(gen_type, context, priority=priority)
