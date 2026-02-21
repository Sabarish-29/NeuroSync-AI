"""
Session Recorder — records all data from an experiment session.

Exports complete session data (events, signals, interventions)
to JSON files for later analysis.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class SessionRecorder:
    """Records and exports experiment session data."""

    def __init__(self, db_manager: Any = None, output_dir: str = "experiment_data"):
        self.db = db_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions: dict[str, dict[str, Any]] = {}

    def start_session(self, session_id: str, metadata: Optional[dict[str, Any]] = None) -> None:
        """Begin recording a session."""
        self._active_sessions[session_id] = {
            "session_id": session_id,
            "started_at": time.time(),
            "metadata": metadata or {},
            "events": [],
            "signals": [],
            "interventions": [],
        }
        logger.info(f"Recording started for session {session_id}")

    def record_event(self, session_id: str, event: dict[str, Any]) -> None:
        """Record an event during a session."""
        if session_id in self._active_sessions:
            event.setdefault("timestamp", time.time())
            self._active_sessions[session_id]["events"].append(event)

    def record_signal(self, session_id: str, signal: dict[str, Any]) -> None:
        """Record a signal snapshot."""
        if session_id in self._active_sessions:
            signal.setdefault("timestamp", time.time())
            self._active_sessions[session_id]["signals"].append(signal)

    def record_intervention(self, session_id: str, intervention: dict[str, Any]) -> None:
        """Record an intervention that fired."""
        if session_id in self._active_sessions:
            intervention.setdefault("timestamp", time.time())
            self._active_sessions[session_id]["interventions"].append(intervention)

    def end_session(self, session_id: str) -> None:
        """Mark session as ended."""
        if session_id in self._active_sessions:
            self._active_sessions[session_id]["ended_at"] = time.time()

    def export_session(self, session_id: str) -> str:
        """Export session data to JSON file. Returns output path."""
        data = self._active_sessions.get(session_id)
        if data is None:
            # Try loading from DB if available
            data = self._load_from_db(session_id)

        if data is None:
            raise ValueError(f"No data for session {session_id}")

        data["export_timestamp"] = time.time()

        output_path = self.output_dir / f"{session_id}.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported session {session_id} → {output_path}")
        return str(output_path)

    def get_session_data(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get in-memory session data."""
        return self._active_sessions.get(session_id)

    @property
    def active_session_ids(self) -> list[str]:
        return list(self._active_sessions.keys())

    def _load_from_db(self, session_id: str) -> Optional[dict[str, Any]]:
        """Load session from database if available."""
        if self.db is None:
            return None

        try:
            events = self.db.fetch_all(
                "SELECT * FROM events WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            )
            interventions = self.db.fetch_all(
                "SELECT * FROM interventions WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            )
            return {
                "session_id": session_id,
                "events": [dict(e) for e in events],
                "signals": [],
                "interventions": [dict(i) for i in interventions],
            }
        except Exception:
            return None
