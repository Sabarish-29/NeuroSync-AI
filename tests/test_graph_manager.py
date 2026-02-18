"""
Tests for GraphManager and NullSession.
"""

import pytest

from neurosync.knowledge.graph_manager import GraphManager, NullSession, NullResult


class TestGraphManagerOffline:
    """Test GraphManager graceful degradation when Neo4j is unavailable."""

    def test_default_not_connected(self):
        """GraphManager starts disconnected."""
        gm = GraphManager()
        assert gm.connected is False
        assert gm.driver is None

    def test_execute_query_offline_returns_empty(self):
        """Queries return empty list when offline."""
        gm = GraphManager()
        result = gm.execute_query("MATCH (n) RETURN n")
        assert result == []

    def test_execute_write_offline_returns_false(self):
        """Writes return False when offline."""
        gm = GraphManager()
        result = gm.execute_write("CREATE (n:Test {id: 'x'})")
        assert result is False

    def test_close_idempotent(self):
        """Closing a never-connected manager doesn't raise."""
        gm = GraphManager()
        gm.close()
        assert gm.connected is False


class TestNullSession:
    """Test the NullSession fallback."""

    def test_null_session_run(self):
        """NullSession.run returns a NullResult."""
        session = NullSession()
        result = session.run("MATCH (n) RETURN n")
        assert isinstance(result, NullResult)

    def test_null_session_context_manager(self):
        """NullSession works as a context manager."""
        with NullSession() as session:
            result = session.run("MATCH (n) RETURN n")
            assert result.data() == []

    def test_null_result_iter(self):
        """NullResult is iterable (empty)."""
        result = NullResult()
        assert list(result) == []

    def test_null_result_single(self):
        """NullResult.single() returns None."""
        result = NullResult()
        assert result.single() is None
