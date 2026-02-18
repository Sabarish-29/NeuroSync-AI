"""
NeuroSync AI — Knowledge Graph Initialisation Script.

Creates the Neo4j schema (constraints + indexes) and seeds base concepts
and prerequisite relationships.

Usage:
    python -m scripts.init_graph [--seed]
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger


def init_schema(graph_manager) -> bool:
    """Execute schema.cypher to create constraints and indexes."""
    from pathlib import Path

    schema_path = Path(__file__).resolve().parent.parent / "neurosync" / "knowledge" / "schema.cypher"

    if not schema_path.exists():
        logger.error("Schema file not found: {}", schema_path)
        return False

    statements = []
    with open(schema_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("//"):
                statements.append(line)

    # Join multi-line statements
    full_text = " ".join(statements)
    queries = [q.strip() + ";" for q in full_text.split(";") if q.strip()]

    success_count = 0
    for query in queries:
        clean = query.rstrip(";").strip()
        if clean and clean.upper().startswith("CREATE"):
            if graph_manager.execute_write(clean):
                success_count += 1
            else:
                logger.warning("Failed to execute: {}", clean[:80])

    logger.info("Schema initialisation complete: {}/{} statements", success_count, len(queries))
    return success_count > 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialise NeuroSync knowledge graph")
    parser.add_argument("--seed", action="store_true", help="Seed concepts and prerequisites")
    parser.add_argument("--uri", default=None, help="Neo4j URI")
    parser.add_argument("--user", default=None, help="Neo4j user")
    parser.add_argument("--password", default=None, help="Neo4j password")
    args = parser.parse_args()

    from neurosync.knowledge.graph_manager import GraphManager

    gm = GraphManager(uri=args.uri, user=args.user, password=args.password)

    if not gm.connect():
        logger.error("Cannot connect to Neo4j — check that the server is running")
        return 1

    try:
        # Create schema
        logger.info("Creating schema...")
        init_schema(gm)

        # Seed data
        if args.seed:
            logger.info("Seeding concepts and prerequisites...")
            from neurosync.knowledge.seeders.prerequisites import seed_all
            counts = seed_all(gm)
            logger.info("Seeded: {} concepts, {} prerequisites", counts["concepts"], counts["prerequisites"])

        logger.info("Knowledge graph initialisation complete!")
        return 0

    finally:
        gm.close()


if __name__ == "__main__":
    sys.exit(main())
