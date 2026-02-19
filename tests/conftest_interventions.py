"""
NeuroSync AI — Intervention test fixtures (Step 6).

Mock OpenAI API responses so tests never call the real API.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from neurosync.interventions.cache.manager import CacheManager
from neurosync.interventions.cost_tracker import CostTracker
from neurosync.interventions.generator import GeneratedContent, InterventionGenerator


# ── Mock OpenAI response objects ────────────────────────────────────


def _make_mock_response(content: str = "This is a test response",
                        prompt_tokens: int = 100,
                        completion_tokens: int = 50) -> MagicMock:
    """Build a mock OpenAI ChatCompletion response."""
    msg = MagicMock()
    msg.content = content

    choice = MagicMock()
    choice.message = msg

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def mock_openai_response() -> MagicMock:
    """Standard mock GPT-4 response."""
    return _make_mock_response()


@pytest.fixture
def cache_manager(tmp_path) -> CacheManager:
    """In-memory cache for tests."""
    return CacheManager(db_path=str(tmp_path / "test_cache.db"), max_size=100)


@pytest.fixture
def cost_tracker() -> CostTracker:
    """Fresh cost tracker with default limits."""
    return CostTracker()


@pytest.fixture
def generator(cache_manager, cost_tracker) -> InterventionGenerator:
    """InterventionGenerator with mocked OpenAI client."""
    gen = InterventionGenerator(
        api_key="sk-test-dummy",
        cache_manager=cache_manager,
        cost_tracker=cost_tracker,
    )
    # Pre-install a mocked client so _get_client() is never called
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_mock_response(),
    )
    gen._client = mock_client
    return gen
