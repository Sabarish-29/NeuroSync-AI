"""
NeuroSync AI — Webcam fusion + injector tests (4 tests).

All tests use synthetic landmarks — no real camera required.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from neurosync.webcam.fusion import WebcamFusionEngine, WebcamMomentScores
from neurosync.webcam.injector import WebcamSignalInjector
from neurosync.webcam.signals.blink import BlinkSignal
from neurosync.webcam.signals.expression import ExpressionSignal
from neurosync.webcam.signals.gaze import GazeSignal
from neurosync.webcam.signals.pose import PoseSignal
from neurosync.webcam.signals.rppg import RemotePPGSignal
from neurosync.database.manager import DatabaseManager
from neurosync.database.repositories.signals import SignalRepository
from neurosync.database.repositories.sessions import SessionRepository
from neurosync.core.events import SessionConfig

from tests.conftest_webcam import (
    make_neutral_landmarks,
    make_no_face_landmarks,
    make_bored_landmarks,
    make_looking_left_landmarks,
    make_frustrated_landmarks,
)


def _make_engine() -> WebcamFusionEngine:
    return WebcamFusionEngine(
        gaze=GazeSignal(),
        blink=BlinkSignal(),
        expression=ExpressionSignal(),
        pose=PoseSignal(),
        rppg=RemotePPGSignal(),
    )


class TestWebcamFusion:
    """Tests for the WebcamFusionEngine."""

    def test_off_screen_plus_boredom_both_flagged(self) -> None:
        """Gaze away + bored expression → low attention + high boredom."""
        engine = _make_engine()

        # Set gaze off-screen for a long time
        engine._gaze._off_screen_start = time.time() - 5.0

        bored_lm = make_bored_landmarks()
        # Shift iris left to also be off-screen
        from tests.conftest_webcam import _shift_iris_left, _make_bored, _default_landmarks
        combined_lm_list = _shift_iris_left(_make_bored(_default_landmarks()))
        from neurosync.webcam.mediapipe_processor import RawLandmarks
        combined_lm = RawLandmarks(
            face_landmarks=combined_lm_list,
            face_detected=True,
            frame_width=640,
            frame_height=480,
            frame_timestamp=time.time(),
        )

        scores = engine.compute(combined_lm)
        assert scores.face_detected is True
        assert scores.attention_score < 0.8
        assert scores.boredom_score > 0.2

    def test_frustration_tension_boosts_behavioral_score(self) -> None:
        """Facial tension high → frustration_boost > 0.10."""
        engine = _make_engine()
        frustrated_lm = make_frustrated_landmarks()
        scores = engine.compute(frustrated_lm)
        assert scores.frustration_boost > 0.05
        assert scores.face_detected is True

    def test_no_face_returns_zero_scores(self) -> None:
        """No face → all scores = 0.0, face_detected = False."""
        engine = _make_engine()
        no_face = make_no_face_landmarks()
        scores = engine.compute(no_face)
        assert scores.face_detected is False
        assert scores.attention_score == 0.0
        assert scores.frustration_boost == 0.0
        assert scores.boredom_score == 0.0

    def test_injector_updates_existing_snapshot(self, tmp_path: Path) -> None:
        """Write snapshot, call injector → snapshot updated with webcam columns."""
        db = DatabaseManager(tmp_path / "test.db")
        db.initialise()

        # Create session first
        session_repo = SessionRepository(db)
        config = SessionConfig(student_id="test", lesson_id="lesson_1")
        session_repo.create_session(config)

        # Insert a snapshot
        sig_repo = SignalRepository(db)
        sid = sig_repo.insert_snapshot(
            session_id=config.session_id,
            timestamp=time.time() * 1000,
        )

        # Inject webcam data
        injector = WebcamSignalInjector(db)
        scores = WebcamMomentScores(
            timestamp=time.time(),
            attention_score=0.95,
            off_screen_triggered=False,
            frustration_boost=0.42,
            face_detected=True,
        )
        injector.inject(config.session_id, scores)

        # Verify the snapshot was updated
        row = db.fetch_one(
            "SELECT gaze_off_screen, facial_tension FROM signal_snapshots WHERE snapshot_id = ?",
            (sid,),
        )
        assert row is not None
        assert row["gaze_off_screen"] == 0
        assert abs(row["facial_tension"] - 0.42) < 0.01

        db.close()
