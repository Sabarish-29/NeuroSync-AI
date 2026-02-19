"""
NeuroSync AI — LangGraph-style fusion graph.

Runs all 8 agents in parallel (via ``asyncio.gather``) on a shared
``FusionState``, then aggregates their proposals into a single list.

The design mirrors a LangGraph ``StateGraph`` but stays lightweight
and dependency-free for the core path — LangGraph itself is available
for advanced routing in production.
"""

from __future__ import annotations

import asyncio
import time
from typing import Sequence

from loguru import logger

from neurosync.fusion.agents.base_agent import BaseAgent
from neurosync.fusion.state import (
    AgentEvaluation,
    AgentState,
    FusionState,
    InterventionProposal,
)


class FusionGraph:
    """
    Parallel-agent graph.  ``execute(state)`` runs every agent and
    returns an updated state with ``proposed_interventions`` populated.
    """

    def __init__(self, agents: Sequence[BaseAgent]) -> None:
        self.agents: dict[str, BaseAgent] = {a.agent_name: a for a in agents}

    # ── public ──────────────────────────────────────────────────────

    async def execute(self, state: FusionState) -> FusionState:
        """Run all agents in parallel and aggregate results."""
        start = time.perf_counter()

        tasks = [
            self._run_agent(name, agent, state)
            for name, agent in self.agents.items()
        ]
        evaluations: list[AgentEvaluation] = await asyncio.gather(
            *tasks, return_exceptions=False,
        )

        # Aggregate proposals + agent states
        all_proposals: list[InterventionProposal] = []
        updated_agent_states: dict[str, AgentState] = {}

        for evaluation in evaluations:
            all_proposals.extend(evaluation.interventions)
            updated_agent_states[evaluation.agent_name] = AgentState(
                agent_name=evaluation.agent_name,
                last_detection_timestamp=(
                    state.timestamp if evaluation.interventions else 0.0
                ),
                detection_count_session=self.agents[
                    evaluation.agent_name
                ].detection_count,
                cooldown_until=0.0,
                active_moments=evaluation.detected_moments,
                confidence=evaluation.confidence,
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.debug(
            "FusionGraph executed {} agents in {:.1f} ms → {} proposals",
            len(self.agents),
            elapsed_ms,
            len(all_proposals),
        )

        # Return updated state (Pydantic model_copy)
        return state.model_copy(
            update={
                "proposed_interventions": all_proposals,
                "agent_states": updated_agent_states,
            },
        )

    # ── internal ────────────────────────────────────────────────────

    @staticmethod
    async def _run_agent(
        name: str,
        agent: BaseAgent,
        state: FusionState,
    ) -> AgentEvaluation:
        """Run a single agent, catching errors gracefully."""
        try:
            return await agent.evaluate(state)
        except Exception as exc:  # noqa: BLE001
            logger.error("Agent {} raised {}: {}", name, type(exc).__name__, exc)
            return AgentEvaluation(
                agent_name=name,
                reasoning=f"Error: {exc}",
            )
