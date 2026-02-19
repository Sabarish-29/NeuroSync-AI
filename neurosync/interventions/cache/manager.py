"""
NeuroSync AI — LRU Cache Manager for generated intervention content.

Two-tier: in-memory dict (fast) + SQLite (persistent across sessions).
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import INTERVENTION_COST_LIMITS


class CacheManager:
    """
    LRU cache backed by SQLite for persistence across sessions.

    Parameters
    ----------
    db_path
        Path to the SQLite cache database.  Pass ``":memory:"`` for tests.
    max_size
        Maximum entries kept in-memory. Oldest are evicted first.
    """

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        max_size: int | None = None,
    ) -> None:
        self.db_path = str(db_path)
        self.max_size = max_size or int(INTERVENTION_COST_LIMITS["CACHE_MAX_SIZE"])
        self._memory_cache: dict[str, Any] = {}
        self._access_order: list[str] = []
        self._init_db()

    # ── DB bootstrap ────────────────────────────────────────────────

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS intervention_cache (
                    cache_key      TEXT PRIMARY KEY,
                    intervention_type TEXT NOT NULL,
                    content        TEXT NOT NULL,
                    tokens_used    INTEGER,
                    created_at     REAL,
                    last_accessed  REAL,
                    access_count   INTEGER DEFAULT 1
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_cache_accessed
                ON intervention_cache(last_accessed)
                """
            )

    # ── async get / set ─────────────────────────────────────────────

    async def get(self, cache_key: str) -> Any | None:
        """Return cached ``GeneratedContent`` or ``None``."""
        # Tier 1 — memory
        if cache_key in self._memory_cache:
            self._update_access_order(cache_key)
            hit = self._memory_cache[cache_key]
            # Always mark returned content as from_cache
            if hasattr(hit, "model_copy"):
                return hit.model_copy(update={"from_cache": True})
            return hit

        # Tier 2 — SQLite
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT intervention_type, content, tokens_used, created_at "
                "FROM intervention_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if row is None:
                return None

            conn.execute(
                "UPDATE intervention_cache SET last_accessed = ?, "
                "access_count = access_count + 1 WHERE cache_key = ?",
                (time.time(), cache_key),
            )

        # Lazy import to avoid circular dependency
        from neurosync.interventions.generator import GeneratedContent

        content = GeneratedContent(
            intervention_type=row[0],
            content=row[1],
            tokens_used=row[2] or 0,
            model="cached",
            from_cache=True,
            generated_at=row[3] or 0.0,
        )
        self._memory_cache[cache_key] = content
        self._update_access_order(cache_key)
        return content

    async def set(self, cache_key: str, content: Any) -> None:
        """Store a ``GeneratedContent`` in both tiers."""
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO intervention_cache
                   (cache_key, intervention_type, content, tokens_used,
                    created_at, last_accessed)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cache_key,
                    content.intervention_type,
                    content.content,
                    content.tokens_used,
                    now,
                    now,
                ),
            )
        self._memory_cache[cache_key] = content
        self._update_access_order(cache_key)

        if len(self._access_order) > self.max_size:
            self._evict_lru()

    # ── LRU bookkeeping ────────────────────────────────────────────

    def _update_access_order(self, cache_key: str) -> None:
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        self._access_order.append(cache_key)

    def _evict_lru(self) -> None:
        while len(self._access_order) > self.max_size:
            lru_key = self._access_order.pop(0)
            self._memory_cache.pop(lru_key, None)

        cutoff = time.time() - (int(INTERVENTION_COST_LIMITS["CACHE_TTL_DAYS"]) * 86400)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM intervention_cache WHERE last_accessed < ?",
                (cutoff,),
            )

    # ── stats ───────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, int]:
        """Return cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM intervention_cache").fetchone()[0]
            total_accesses = (
                conn.execute("SELECT SUM(access_count) FROM intervention_cache").fetchone()[0]
                or 0
            )
        return {
            "total_entries": total,
            "memory_entries": len(self._memory_cache),
            "total_accesses": total_accesses,
        }
