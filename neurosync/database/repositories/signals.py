"""
NeuroSync AI — Signal snapshot and mastery repository.

Stores computed signal snapshots and mastery records.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from loguru import logger

from neurosync.core.events import InterventionRequest
from neurosync.database.manager import DatabaseManager


class SignalRepository:
    """Repository for signal snapshots, interventions, mastery records, and session summaries."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def insert_snapshot(
        self,
        session_id: str,
        timestamp: float,
        *,
        response_time_mean_ms: Optional[float] = None,
        response_time_trend: Optional[str] = None,
        fast_answer_rate: Optional[float] = None,
        rewinds_per_minute: Optional[float] = None,
        rewind_burst: bool = False,
        idle_frequency: Optional[float] = None,
        interaction_variance: Optional[float] = None,
        scroll_pattern: Optional[str] = None,
        frustration_score: Optional[float] = None,
        fatigue_score: Optional[float] = None,
        gaze_off_screen: Optional[bool] = None,
        blink_rate: Optional[float] = None,
        facial_tension: Optional[float] = None,
        alpha_power: Optional[float] = None,
        beta_power: Optional[float] = None,
        theta_power: Optional[float] = None,
        active_moments: Optional[list[str]] = None,
    ) -> str:
        """Insert a signal snapshot."""
        snapshot_id = str(uuid.uuid4())
        self._db.execute(
            """INSERT INTO signal_snapshots
               (snapshot_id, session_id, timestamp,
                response_time_mean_ms, response_time_trend, fast_answer_rate,
                rewinds_per_minute, rewind_burst, idle_frequency,
                interaction_variance, scroll_pattern,
                frustration_score, fatigue_score,
                gaze_off_screen, blink_rate, facial_tension,
                alpha_power, beta_power, theta_power,
                active_moments)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot_id, session_id, timestamp,
                response_time_mean_ms, response_time_trend, fast_answer_rate,
                rewinds_per_minute, int(rewind_burst), idle_frequency,
                interaction_variance, scroll_pattern,
                frustration_score, fatigue_score,
                int(gaze_off_screen) if gaze_off_screen is not None else None,
                blink_rate, facial_tension,
                alpha_power, beta_power, theta_power,
                json.dumps(active_moments) if active_moments else "[]",
            ),
        )
        logger.debug("Signal snapshot saved: {}", snapshot_id)
        return snapshot_id

    def insert_intervention(self, session_id: str, intervention: InterventionRequest) -> str:
        """Record an intervention that was fired."""
        intervention_id = str(uuid.uuid4())
        self._db.execute(
            """INSERT INTO interventions
               (intervention_id, session_id, timestamp, moment_id,
                intervention_type, urgency, payload, confidence,
                signals_triggered, student_acknowledged)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                intervention_id,
                session_id,
                intervention.payload.get("timestamp", 0.0),
                intervention.moment_id,
                intervention.intervention_type,
                intervention.urgency,
                json.dumps(intervention.payload, default=str),
                intervention.confidence,
                json.dumps(intervention.signals_triggered),
                0,
            ),
        )
        logger.info("Intervention recorded: {} ({})", intervention.moment_id, intervention.intervention_type)
        return intervention_id

    def upsert_mastery(
        self,
        student_id: str,
        concept_id: str,
        authenticity_score: float,
        timestamp: float,
    ) -> None:
        """Insert or update a mastery record for a student-concept pair."""
        record_id = str(uuid.uuid4())
        self._db.execute(
            """INSERT INTO mastery_records
               (record_id, student_id, concept_id, first_mastered_at,
                last_tested_at, authenticity_score, review_count, retention_history)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?)
               ON CONFLICT(student_id, concept_id) DO UPDATE SET
                   last_tested_at = excluded.last_tested_at,
                   authenticity_score = excluded.authenticity_score,
                   review_count = review_count + 1""",
            (
                record_id, student_id, concept_id, timestamp,
                timestamp, authenticity_score,
                json.dumps([[timestamp, authenticity_score]]),
            ),
        )
        logger.debug("Mastery upserted: {} / {}", student_id, concept_id)

    def get_mastery(self, student_id: str, concept_id: str) -> Optional[dict[str, Any]]:
        """Get mastery record for a student-concept pair."""
        row = self._db.fetch_one(
            "SELECT * FROM mastery_records WHERE student_id = ? AND concept_id = ?",
            (student_id, concept_id),
        )
        if row is None:
            return None
        return dict(row)

    def get_session_snapshots(self, session_id: str) -> list[dict[str, Any]]:
        """Get all signal snapshots for a session."""
        rows = self._db.fetch_all(
            "SELECT * FROM signal_snapshots WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        return [dict(r) for r in rows]
