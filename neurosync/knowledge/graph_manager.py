"""
NeuroSync AI — Neo4j Graph Manager.

Manages the Neo4j driver lifecycle, provides session factories, and
implements graceful degradation when Neo4j is unavailable.

All graph operations go through this manager. When the database is
unreachable, methods return safe defaults rather than raising exceptions.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import NEO4J_CONFIG


class GraphManager:
    """
    Neo4j connection manager with automatic retry and graceful degradation.

    Usage::

        gm = GraphManager()
        gm.connect()
        with gm.session() as session:
            result = session.run("MATCH (n:Concept) RETURN n LIMIT 5")
        gm.close()
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        self._uri = uri or str(NEO4J_CONFIG["URI"])
        self._user = user or str(NEO4J_CONFIG["USER"])
        self._password = password or str(NEO4J_CONFIG["PASSWORD"])
        self._database = database or str(NEO4J_CONFIG["DATABASE"])
        self._driver: Any = None
        self._connected = False
        self._retry_attempts = int(NEO4J_CONFIG["RETRY_ATTEMPTS"])
        self._retry_delay = float(NEO4J_CONFIG["RETRY_DELAY_SECONDS"])
        logger.debug("GraphManager initialised (uri={})", self._uri)

    @property
    def connected(self) -> bool:
        """Whether the manager has an active connection to Neo4j."""
        return self._connected

    @property
    def driver(self) -> Any:
        """Return the underlying Neo4j driver (or None)."""
        return self._driver

    def connect(self) -> bool:
        """
        Establish connection to Neo4j with retry logic.

        Returns True if connection succeeded, False otherwise.
        """
        try:
            from neo4j import GraphDatabase  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("neo4j package not installed — running in offline mode")
            return False

        for attempt in range(1, self._retry_attempts + 1):
            try:
                self._driver = GraphDatabase.driver(
                    self._uri,
                    auth=(self._user, self._password),
                    max_connection_pool_size=int(NEO4J_CONFIG["MAX_CONNECTION_POOL_SIZE"]),
                    connection_timeout=int(NEO4J_CONFIG["CONNECTION_TIMEOUT_SECONDS"]),
                )
                # Verify connectivity
                self._driver.verify_connectivity()
                self._connected = True
                logger.info("Connected to Neo4j at {} (attempt {})", self._uri, attempt)
                return True
            except Exception as exc:
                logger.warning(
                    "Neo4j connection attempt {}/{} failed: {}",
                    attempt, self._retry_attempts, exc,
                )
                if attempt < self._retry_attempts:
                    time.sleep(self._retry_delay)

        logger.error("All Neo4j connection attempts failed — running in offline mode")
        self._connected = False
        return False

    def session(self, **kwargs: Any) -> Any:
        """
        Create a Neo4j session.

        Falls back to a NullSession if not connected.
        """
        if not self._connected or self._driver is None:
            return NullSession()
        return self._driver.session(database=self._database, **kwargs)

    def execute_query(self, cypher: str, parameters: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results as list of dicts.

        Returns empty list on failure (graceful degradation).
        """
        if not self._connected:
            logger.debug("Graph offline — skipping query: {}", cypher[:80])
            return []

        try:
            with self.session() as session:
                result = session.run(cypher, parameters or {})
                return [record.data() for record in result]
        except Exception as exc:
            logger.warning("Graph query failed: {} — {}", cypher[:60], exc)
            return []

    def execute_write(self, cypher: str, parameters: Optional[dict[str, Any]] = None) -> bool:
        """
        Execute a write Cypher query. Returns True on success.

        Returns False on failure (graceful degradation).
        """
        if not self._connected:
            logger.debug("Graph offline — skipping write: {}", cypher[:80])
            return False

        try:
            with self.session() as session:
                session.run(cypher, parameters or {})
            return True
        except Exception as exc:
            logger.warning("Graph write failed: {} — {}", cypher[:60], exc)
            return False

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            try:
                self._driver.close()
            except Exception:  # noqa: BLE001
                pass
            self._driver = None
        self._connected = False
        logger.info("GraphManager connection closed")

    def __enter__(self) -> GraphManager:
        self.connect()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class NullSession:
    """
    A no-op session used when Neo4j is unavailable.

    Allows code to proceed without raising exceptions.
    """

    def run(self, _cypher: str, _params: Optional[dict[str, Any]] = None, **_kw: Any) -> NullResult:
        return NullResult()

    def __enter__(self) -> NullSession:
        return self

    def __exit__(self, *_: Any) -> None:
        pass


class NullResult:
    """No-op query result returned by NullSession."""

    def data(self) -> list[dict[str, Any]]:
        return []

    def __iter__(self):  # type: ignore[override]
        return iter([])

    def single(self) -> None:
        return None
