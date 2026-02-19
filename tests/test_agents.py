"""
Step 5 — Agent unit tests (16 tests, 2 per agent).
"""

from __future__ import annotations

import pytest

from neurosync.fusion.agents.attention_agent import AttentionAgent
from neurosync.fusion.agents.engagement_agent import EngagementAgent
from neurosync.fusion.agents.fatigue_agent import FatigueAgent
from neurosync.fusion.agents.gap_agent import GapAgent
from neurosync.fusion.agents.memory_agent import MemoryAgent
from neurosync.fusion.agents.misconception_agent import MisconceptionAgent
from neurosync.fusion.agents.overload_agent import OverloadAgent
from neurosync.fusion.agents.plateau_agent import PlateauAgent
from neurosync.fusion.state import FusionState


# ── Attention Agent ─────────────────────────────────────────────────


class TestAttentionAgent:

    @pytest.mark.asyncio
    async def test_fires_on_gaze_off(self, attention_drop_state: FusionState):
        """Off-screen → pause_video intervention."""
        agent = AttentionAgent()
        result = await agent.evaluate(attention_drop_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "pause_video"
        assert result.interventions[0].urgency == "high"

    @pytest.mark.asyncio
    async def test_cooldown_respected(self, attention_drop_state: FusionState):
        """Agent on cooldown → no intervention even if off-screen."""
        agent = AttentionAgent()
        # Fire once
        await agent.evaluate(attention_drop_state)
        # Second call should be on cooldown
        result = await agent.evaluate(attention_drop_state)
        assert len(result.interventions) == 0
        assert "M01" in result.detected_moments


# ── Overload Agent ──────────────────────────────────────────────────


class TestOverloadAgent:

    @pytest.mark.asyncio
    async def test_fires_on_nlp_complexity(self, overload_state: FusionState):
        """NLP overload → simplify_phrase."""
        agent = OverloadAgent()
        result = await agent.evaluate(overload_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "simplify_phrase"

    @pytest.mark.asyncio
    async def test_per_phrase_cooldown(self, overload_state: FusionState):
        """Same phrase simplified already → no duplicate."""
        agent = OverloadAgent()
        await agent.evaluate(overload_state)
        result = await agent.evaluate(overload_state)
        assert len(result.interventions) == 0


# ── Gap Agent ───────────────────────────────────────────────────────


class TestGapAgent:

    @pytest.mark.asyncio
    async def test_fires_on_unknown_concept(self, gap_state: FusionState):
        """Pending gaps → explain_concept for each."""
        agent = GapAgent()
        result = await agent.evaluate(gap_state)
        assert len(result.interventions) == 2
        assert all(i.intervention_type == "explain_concept" for i in result.interventions)

    @pytest.mark.asyncio
    async def test_skips_already_explained(self, gap_state: FusionState):
        """Gap already explained → skip."""
        agent = GapAgent()
        await agent.evaluate(gap_state)
        result = await agent.evaluate(gap_state)
        assert len(result.interventions) == 0


# ── Engagement Agent ────────────────────────────────────────────────


class TestEngagementAgent:

    @pytest.mark.asyncio
    async def test_fires_frustration_critical(self, frustration_critical_state: FusionState):
        """Frustration > 0.70 → rescue_frustration."""
        agent = EngagementAgent()
        result = await agent.evaluate(frustration_critical_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "rescue_frustration"
        assert result.interventions[0].urgency == "critical"

    @pytest.mark.asyncio
    async def test_fires_boredom(self, boredom_state: FusionState):
        """High mastery + webcam boredom → skip_to_challenge."""
        agent = EngagementAgent()
        result = await agent.evaluate(boredom_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "skip_to_challenge"

    @pytest.mark.asyncio
    async def test_fires_confidence_collapse(self, confidence_collapse_state: FusionState):
        """Moderate frustration → show_knowledge_mirror."""
        agent = EngagementAgent()
        result = await agent.evaluate(confidence_collapse_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "show_knowledge_mirror"

    @pytest.mark.asyncio
    async def test_prioritises_frustration_over_boredom(
        self, frustration_critical_state: FusionState,
    ):
        """Frustration critical wins over boredom even if mastery is high."""
        agent = EngagementAgent()
        # Override mastery to trigger boredom too
        state = frustration_critical_state.model_copy(
            update={"knowledge": frustration_critical_state.knowledge.model_copy(
                update={"current_segment_mastery": 0.95},
            )},
        )
        result = await agent.evaluate(state)
        # Frustration branch fires first (elif prevents boredom)
        assert any(i.intervention_type == "rescue_frustration" for i in result.interventions)


# ── Fatigue Agent ───────────────────────────────────────────────────


class TestFatigueAgent:

    @pytest.mark.asyncio
    async def test_fires_mandatory_break(self, fatigue_critical_state: FusionState):
        """Fatigue > 0.75 → force_break."""
        agent = FatigueAgent()
        result = await agent.evaluate(fatigue_critical_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "force_break"
        assert result.interventions[0].urgency == "critical"

    @pytest.mark.asyncio
    async def test_respects_break_cooldown(self, fatigue_critical_state: FusionState):
        """Just had a break → no duplicate force_break."""
        agent = FatigueAgent()
        await agent.evaluate(fatigue_critical_state)
        result = await agent.evaluate(fatigue_critical_state)
        assert len(result.interventions) == 0
        assert "M10" in result.detected_moments


# ── Memory Agent ────────────────────────────────────────────────────


class TestMemoryAgent:

    @pytest.mark.asyncio
    async def test_fires_on_overflow(self, memory_overflow_state: FusionState):
        """Overflow risk → checkpoint_concepts."""
        agent = MemoryAgent()
        result = await agent.evaluate(memory_overflow_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "checkpoint_concepts"


# ── Misconception Agent ─────────────────────────────────────────────


class TestMisconceptionAgent:

    @pytest.mark.asyncio
    async def test_fires_on_conflict(self, misconception_state: FusionState):
        """Pending misconception → clear_misconception."""
        agent = MisconceptionAgent()
        result = await agent.evaluate(misconception_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "clear_misconception"


# ── Plateau Agent ───────────────────────────────────────────────────


class TestPlateauAgent:

    @pytest.mark.asyncio
    async def test_fires_after_3_failures(self, plateau_state: FusionState):
        """Plateau detected → method_overhaul."""
        agent = PlateauAgent()
        result = await agent.evaluate(plateau_state)
        assert len(result.interventions) == 1
        assert result.interventions[0].intervention_type == "method_overhaul"

    @pytest.mark.asyncio
    async def test_tracks_switched_concepts(self, plateau_state: FusionState):
        """Method already switched → no duplicate overhaul."""
        agent = PlateauAgent()
        await agent.evaluate(plateau_state)
        result = await agent.evaluate(plateau_state)
        assert len(result.interventions) == 0
        assert "M22" in result.detected_moments
