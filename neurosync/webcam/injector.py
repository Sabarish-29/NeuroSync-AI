"""
NeuroSync AI — Webcam signal injector.

Bridges webcam signals into Step 1's ``signal_snapshots`` table.  The
behavioral fusion engine already reads those columns — so the moment
webcam data appears there, all 22 moment detectors gain visual context
with NO changes to Step 1 code.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from neurosync.database.manager import DatabaseManager
from neurosync.webcam.fusion import WebcamMomentScores


class WebcamSignalInjector:
    """
    Writes webcam columns into the most recent ``signal_snapshots`` row.

    Called once per second by the webcam fusion loop.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager
        logger.debug("WebcamSignalInjector initialised")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def inject(self, session_id: str, scores: WebcamMomentScores) -> None:
        """
        UPDATE the most recent signal-snapshot row with webcam values.

        If no snapshot exists yet for this session the call is silently
        skipped (first few seconds of a session).
        """
        gaze_off = 1 if scores.off_screen_triggered else 0
        facial_tension = scores.frustration_boost  # best proxy for "facial tension"

        try:
            self._db.execute(
                """
                UPDATE signal_snapshots
                SET gaze_off_screen = ?,
                    blink_rate      = ?,
                    facial_tension  = ?
                WHERE session_id = ?
                  AND snapshot_id = (
                      SELECT snapshot_id
                      FROM signal_snapshots
                      WHERE session_id = ?
                      ORDER BY timestamp DESC
                      LIMIT 1
                  )
                """,
                (
                    gaze_off,
                    scores.attention_score,   # attention as proxy for blink_rate column
                    facial_tension,
                    session_id,
                    session_id,
                ),
            )
            logger.debug(
                "Webcam injected → gaze_off={}, tension={:.3f}",
                gaze_off,
                facial_tension,
            )
        except Exception as exc:
            logger.warning("Webcam inject failed: {}", exc)

    def trigger_immediate_m01(self, session_id: str, duration_ms: float) -> None:
        """
        Fast-path for M01 attention drop when gaze has been off-screen
        beyond the threshold.  Marks latest snapshot with
        ``gaze_off_screen = 1`` so the behavioral fusion engine picks
        it up on its very next cycle.
        """
        try:
            self._db.execute(
                """
                UPDATE signal_snapshots
                SET gaze_off_screen = 1
                WHERE session_id = ?
                  AND snapshot_id = (
                      SELECT snapshot_id
                      FROM signal_snapshots
                      WHERE session_id = ?
                      ORDER BY timestamp DESC
                      LIMIT 1
                  )
                """,
                (session_id, session_id),
            )
            logger.info("M01 immediate trigger — off-screen {:.0f}ms", duration_ms)
        except Exception as exc:
            logger.warning("M01 trigger failed: {}", exc)
