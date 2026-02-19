"""
Tests for CacheManager (Step 6) — 4 tests.
"""

from __future__ import annotations

import pytest

from neurosync.interventions.cache.manager import CacheManager
from neurosync.interventions.generator import GeneratedContent


def _make_content(itype: str = "explain", text: str = "Test content") -> GeneratedContent:
    return GeneratedContent(
        intervention_type=itype,
        content=text,
        tokens_used=100,
        model="gpt-4-turbo-preview",
        from_cache=False,
    )


@pytest.mark.asyncio
async def test_cache_stores_and_retrieves(cache_manager: CacheManager):
    """Set content → get content → matches."""
    content = _make_content()
    await cache_manager.set("key1", content)
    cached = await cache_manager.get("key1")
    assert cached is not None
    assert cached.content == "Test content"
    assert cached.from_cache is True  # DB reconstruction marks as cached


@pytest.mark.asyncio
async def test_cache_updates_access_tracking(cache_manager: CacheManager):
    """Get content twice → access_count incremented."""
    content = _make_content()
    await cache_manager.set("key2", content)

    # Clear memory so second get hits DB and increments access_count
    cache_manager._memory_cache.clear()
    cache_manager._access_order.clear()

    await cache_manager.get("key2")
    cache_manager._memory_cache.clear()
    cache_manager._access_order.clear()

    await cache_manager.get("key2")

    stats = cache_manager.get_stats()
    # 1 initial insert + 2 DB reads = access_count around 3
    assert stats["total_accesses"] >= 3


@pytest.mark.asyncio
async def test_cache_evicts_lru_when_full(tmp_path):
    """Cache max_size=5, add 7 items → oldest evicted from memory."""
    cm = CacheManager(db_path=str(tmp_path / "evict.db"), max_size=5)
    for i in range(7):
        await cm.set(f"k{i}", _make_content(text=f"content-{i}"))

    # Memory should have at most 5
    assert len(cm._memory_cache) <= 5
    # But DB still has all 7
    stats = cm.get_stats()
    assert stats["total_entries"] == 7


@pytest.mark.asyncio
async def test_cache_get_stats_accurate(cache_manager: CacheManager):
    """Various operations → stats reflect reality."""
    assert cache_manager.get_stats()["total_entries"] == 0

    await cache_manager.set("a", _make_content(text="alpha"))
    await cache_manager.set("b", _make_content(text="beta"))

    stats = cache_manager.get_stats()
    assert stats["total_entries"] == 2
    assert stats["memory_entries"] == 2
