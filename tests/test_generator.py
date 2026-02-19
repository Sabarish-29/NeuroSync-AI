"""
Tests for the main InterventionGenerator (Step 6) — 6 tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest_interventions import _make_mock_response
from neurosync.interventions.generator import GeneratedContent, InterventionGenerator


EXPLAIN_CTX = {
    "concept_name": "photosynthesis",
    "lesson_topic": "biology",
    "grade_level": 8,
}


@pytest.mark.asyncio
async def test_generator_calls_gpt4_on_cache_miss(generator: InterventionGenerator):
    """Cache empty → GPT-4 called → response cached."""
    result = await generator.generate("explain", EXPLAIN_CTX)

    assert isinstance(result, GeneratedContent)
    assert result.intervention_type == "explain"
    assert result.content == "This is a test response"
    assert result.from_cache is False
    generator._client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_generator_returns_cached_on_hit(generator: InterventionGenerator):
    """Cache has entry → GPT-4 NOT called → cached content returned."""
    # First call populates cache
    await generator.generate("explain", EXPLAIN_CTX)
    generator._client.chat.completions.create.reset_mock()

    # Second call should hit cache
    result = await generator.generate("explain", EXPLAIN_CTX)
    assert result.from_cache is True
    generator._client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_generator_uses_fallback_on_cost_limit(generator: InterventionGenerator):
    """Cost limit exceeded → fallback template used."""
    generator.cost_tracker.session_cost = generator.cost_tracker.session_limit + 1
    result = await generator.generate("rescue", {"concept_name": "algebra"})
    assert result.model == "fallback_template"


@pytest.mark.asyncio
async def test_generator_uses_fallback_on_rate_limit(generator: InterventionGenerator):
    """Rate limit exceeded → fallback template used."""
    generator.request_count = generator.max_requests_per_minute + 1
    generator.request_window_start = __import__("time").time()  # current window
    result = await generator.generate("explain", EXPLAIN_CTX, priority="normal")
    assert result.model == "fallback_template"


@pytest.mark.asyncio
async def test_generator_retries_on_api_error(generator: InterventionGenerator):
    """API fails twice, succeeds on 3rd try → response returned."""
    ok_resp = _make_mock_response("Recovered response")
    generator._client.chat.completions.create = AsyncMock(
        side_effect=[RuntimeError("fail1"), RuntimeError("fail2"), ok_resp],
    )
    result = await generator.generate("explain", EXPLAIN_CTX)
    assert result.content == "Recovered response"
    assert generator._client.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_generator_uses_fallback_after_max_retries(generator: InterventionGenerator):
    """API fails 3 times → fallback template used."""
    generator._client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("permanent failure"),
    )
    result = await generator.generate("explain", EXPLAIN_CTX)
    assert result.model == "fallback_template"
