"""
System Validation and Health Check.

Provides clear feedback about which features are operational:
  - CORE (must work): Groq LLM, behavioral signals
  - OPTIONAL: webcam, EEG, Neo4j
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger


class SystemValidator:
    """
    Validates system configuration and dependencies.

    ``validate_all()`` returns a structured dict with core / optional
    status, warnings, errors, and an overall status string.
    """

    @staticmethod
    def validate_all() -> dict[str, Any]:
        results: dict[str, Any] = {
            "core": {},
            "optional": {},
            "status": "ready",
            "warnings": [],
            "errors": [],
            "message": "",
        }

        # ── CORE ──────────────────────────────────────────────────────

        # Groq API
        groq_key = os.getenv("GROQ_API_KEY", "")
        results["core"]["groq"] = len(groq_key) > 10
        if not results["core"]["groq"]:
            results["errors"].append(
                "GROQ_API_KEY not set (get free at console.groq.com/keys)"
            )

        # Behavioral signals — always available (internal)
        results["core"]["behavioral"] = True

        # ── OPTIONAL ──────────────────────────────────────────────────

        # Webcam
        try:
            import cv2  # noqa: F401

            results["optional"]["webcam"] = True
        except Exception:
            results["optional"]["webcam"] = False
            results["warnings"].append("OpenCV not installed — webcam features unavailable (optional)")

        # EEG
        eeg_enabled = os.getenv("EEG_ENABLED", "false").lower() == "true"
        if eeg_enabled:
            try:
                from neurosync.eeg.coordinator import EEGCoordinator

                coord = EEGCoordinator(enabled=True)
                if coord.initialize():
                    results["optional"]["eeg"] = True
                    coord.shutdown()
                else:
                    results["optional"]["eeg"] = False
                    results["warnings"].append("EEG enabled but hardware not connected (optional)")
            except Exception as exc:
                results["optional"]["eeg"] = False
                results["warnings"].append(f"EEG module error: {exc} (optional)")
        else:
            results["optional"]["eeg"] = False

        # Neo4j
        try:
            from neo4j import GraphDatabase

            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            results["optional"]["neo4j"] = True
            driver.close()
        except Exception:
            results["optional"]["neo4j"] = False
            results["warnings"].append("Neo4j not available — knowledge graph features limited (optional)")

        # ── overall status ────────────────────────────────────────────

        core_ok = all(results["core"].values())
        if not core_ok:
            results["status"] = "broken"
            results["message"] = f"Core features not working. Errors: {results['errors']}"
        elif results["warnings"]:
            results["status"] = "degraded"
            results["message"] = (
                f"System working with {len(results['warnings'])} optional "
                f"feature(s) unavailable. Core features OK."
            )
        else:
            results["status"] = "ready"
            results["message"] = "All systems operational"

        return results

    @staticmethod
    def print_status_report() -> bool:
        """Print human-readable status report; return ``True`` if usable."""
        results = SystemValidator.validate_all()

        print("\n" + "=" * 60)
        print("NEUROSYNC v5.1 SYSTEM STATUS")
        print("=" * 60)

        print("\nCORE FEATURES (Required):")
        for comp, ok in results["core"].items():
            print(f"  {'OK' if ok else 'FAIL':>4}  {comp.upper()}")

        print("\nOPTIONAL ENHANCEMENTS:")
        for comp, ok in results["optional"].items():
            note = "" if ok else "  (not enabled)"
            print(f"  {'OK' if ok else 'N/A':>4}  {comp.upper()}{note}")

        for w in results["warnings"]:
            print(f"\n  WARN  {w}")
        for e in results["errors"]:
            print(f"\n  ERR   {e}")

        print(f"\nSTATUS: {results['status'].upper()}")
        print(results["message"])
        print("=" * 60 + "\n")

        return results["status"] in ("ready", "degraded")


if __name__ == "__main__":
    import sys

    ok = SystemValidator.print_status_report()
    sys.exit(0 if ok else 1)
