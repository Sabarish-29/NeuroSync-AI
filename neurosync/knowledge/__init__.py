"""
NeuroSync AI — Knowledge Graph Layer (Step 3).

Neo4j-backed concept graph for tracking student mastery, prerequisites,
misconceptions, and powering knowledge-aware moment detectors.
"""

from neurosync.knowledge.graph_manager import GraphManager

__all__ = ["GraphManager"]
