"""
Patent Evidence Logger.

Logs all moment detections with metadata to create an evidence trail
demonstrating reduction to practice of patent claims.

Records:
- Moment detections (all 22 types)
- Confidence calculations (primary + EEG boost)
- EEG quality decisions (use vs fallback)
- Threshold applications
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class PatentLogger:
    """
    Logs patent-defensible evidence of system operation.

    Creates timestamped JSONL records of moment detections,
    confidence calculations, EEG quality decisions, and
    threshold applications.

    Storage: JSONL (one JSON object per line) for append-only,
    streaming-friendly, corruption-resistant logging.
    """

    def __init__(self, log_dir: str = "logs/patent_defense") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"patent_evidence_{today}.jsonl"
        logger.debug("Patent logger → {}", self.log_file)

    # ── public logging methods ──────────────────────────────────────

    def log_moment_detection(
        self,
        moment_id: str,
        detected: bool,
        primary_confidence: float,
        eeg_boost: float,
        total_confidence: float,
        signals_used: Dict[str, bool],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a moment detection event."""
        self._write({
            "event": "moment_detection",
            "moment_id": moment_id,
            "detected": detected,
            "confidence": {
                "primary": round(primary_confidence, 4),
                "eeg_boost": round(eeg_boost, 4),
                "total": round(total_confidence, 4),
            },
            "signals": signals_used,
            "metadata": metadata or {},
        })

    def log_eeg_quality_decision(
        self,
        quality_score: float,
        threshold: float,
        decision: str,
        reason: Optional[str] = None,
    ) -> None:
        """Log an EEG quality gating decision ("use" or "fallback")."""
        self._write({
            "event": "eeg_quality_decision",
            "quality": round(quality_score, 4),
            "threshold": threshold,
            "decision": decision,
            "reason": reason,
        })

    def log_threshold_application(
        self,
        detector_id: str,
        threshold_name: str,
        threshold_value: float,
        measured_value: float,
        condition_met: bool,
    ) -> None:
        """Log a threshold comparison event."""
        self._write({
            "event": "threshold_application",
            "detector": detector_id,
            "threshold_name": threshold_name,
            "threshold_value": threshold_value,
            "measured": round(measured_value, 4),
            "met": condition_met,
        })

    def log_confidence_fusion(
        self,
        moment_id: str,
        primary_sources: Dict[str, float],
        eeg_contribution: float,
        fusion_method: str,
        final_confidence: float,
    ) -> None:
        """Log a confidence fusion calculation."""
        self._write({
            "event": "confidence_fusion",
            "moment_id": moment_id,
            "primary_sources": {k: round(v, 4) for k, v in primary_sources.items()},
            "eeg_contribution": round(eeg_contribution, 4),
            "method": fusion_method,
            "final": round(final_confidence, 4),
        })

    # ── query ───────────────────────────────────────────────────────

    def query_logs(
        self,
        event_type: Optional[str] = None,
        moment_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Dict[str, Any]]:
        """Return matching records from today's log file."""
        records: list[Dict[str, Any]] = []
        try:
            with open(self.log_file) as f:
                for line in f:
                    if len(records) >= limit:
                        break
                    record = json.loads(line)
                    if event_type and record.get("event") != event_type:
                        continue
                    if moment_id and record.get("moment_id") != moment_id:
                        continue
                    records.append(record)
        except FileNotFoundError:
            pass
        return records

    # ── internal ────────────────────────────────────────────────────

    def _write(self, payload: Dict[str, Any]) -> None:
        payload["timestamp"] = time.time()
        payload["datetime"] = datetime.now().isoformat()
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as exc:
            logger.error("Patent log write failed: {}", exc)


# ── module-level singleton & convenience functions ──────────────────

_patent_logger: Optional[PatentLogger] = None


def get_patent_logger() -> PatentLogger:
    """Get or create the global patent logger instance."""
    global _patent_logger
    if _patent_logger is None:
        _patent_logger = PatentLogger()
    return _patent_logger


def reset_patent_logger() -> None:
    """Reset the global instance (useful for tests)."""
    global _patent_logger
    _patent_logger = None


def log_moment_detection(*args: Any, **kwargs: Any) -> None:
    get_patent_logger().log_moment_detection(*args, **kwargs)


def log_eeg_quality_decision(*args: Any, **kwargs: Any) -> None:
    get_patent_logger().log_eeg_quality_decision(*args, **kwargs)


def log_threshold_application(*args: Any, **kwargs: Any) -> None:
    get_patent_logger().log_threshold_application(*args, **kwargs)


def log_confidence_fusion(*args: Any, **kwargs: Any) -> None:
    get_patent_logger().log_confidence_fusion(*args, **kwargs)
