"""Phase 4 integration tests — patent logging in detectors."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from neurosync.fusion.moment_detectors.base_detector import (
    BaseMomentDetector,
    MomentDetectionResult,
)
from neurosync.fusion.moment_detectors.m01_attention import M01AttentionDetector
from neurosync.fusion.moment_detectors.m02_cognitive_load import M02CognitiveLoadDetector
from neurosync.fusion.moment_detectors.m10_fatigue import M10FatigueDetector
from neurosync.fusion.state import (
    BehavioralSignals,
    EEGSignals,
    FusionState,
    WebcamSignals,
)
from neurosync.utils.patent_logger import PatentLogger, reset_patent_logger


@pytest.fixture(autouse=True)
def _isolate_patent_logger(tmp_path: Path):
    """Redirect patent logger to tmp dir so tests don't pollute disk."""
    reset_patent_logger()
    with patch(
        "neurosync.fusion.moment_detectors.base_detector.log_moment_detection"
    ) as mock_log, patch(
        "neurosync.fusion.moment_detectors.base_detector.log_eeg_quality_decision"
    ) as mock_eeg_log:
        yield mock_log, mock_eeg_log
    reset_patent_logger()


class TestPatentLoggingIntegration:
    """Verify that detectors call patent logging functions."""

    def test_m01_detection_calls_patent_log(self, _isolate_patent_logger) -> None:
        mock_log, _ = _isolate_patent_logger
        detector = M01AttentionDetector()
        state = FusionState(
            student_id="s1",
            session_id="sess1",
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=5000),
            behavioral=BehavioralSignals(idle_frequency=1.5),
        )
        result = detector.detect(state)
        assert result is not None
        assert result.detected
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args
        assert call_kwargs[1]["moment_id"] == "M01" or call_kwargs[0][0] == "M01"

    def test_m02_detection_calls_patent_log(self, _isolate_patent_logger) -> None:
        mock_log, _ = _isolate_patent_logger
        detector = M02CognitiveLoadDetector()
        state = FusionState(
            student_id="s1",
            session_id="sess1",
            behavioral=BehavioralSignals(rewind_burst=True),
            webcam=WebcamSignals(frustration_boost=0.75),
        )
        result = detector.detect(state)
        assert result is not None
        mock_log.assert_called_once()

    def test_no_log_when_not_detected(self, _isolate_patent_logger) -> None:
        mock_log, _ = _isolate_patent_logger
        detector = M01AttentionDetector()
        state = FusionState(
            student_id="s1",
            session_id="sess1",
            webcam=WebcamSignals(attention_score=0.90),
            behavioral=BehavioralSignals(),
        )
        result = detector.detect(state)
        assert result is None
        mock_log.assert_not_called()

    def test_eeg_quality_decision_logged(self, _isolate_patent_logger) -> None:
        _, mock_eeg_log = _isolate_patent_logger
        detector = M01AttentionDetector()
        state = FusionState(
            student_id="s1",
            session_id="sess1",
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=5000),
            behavioral=BehavioralSignals(idle_frequency=1.5),
            eeg=EEGSignals(quality=0.85, alpha_power=0.5),
        )
        detector.detect(state)
        mock_eeg_log.assert_called_once()
        args = mock_eeg_log.call_args
        # Should log EEG quality decision with "use"
        assert args[0][2] == "use" or args[1].get("decision") == "use"

    def test_eeg_fallback_logged_on_low_quality(self, _isolate_patent_logger) -> None:
        _, mock_eeg_log = _isolate_patent_logger
        detector = M01AttentionDetector()
        state = FusionState(
            student_id="s1",
            session_id="sess1",
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=5000),
            behavioral=BehavioralSignals(idle_frequency=1.5),
            eeg=EEGSignals(quality=0.30),
        )
        detector.detect(state)
        mock_eeg_log.assert_called_once()
        args = mock_eeg_log.call_args
        assert args[0][2] == "fallback" or args[1].get("decision") == "fallback"


class TestPatentLoggerFileOutput:
    """Verify actual file output from patent logger."""

    def test_jsonl_records_are_valid_json(self, tmp_path: Path) -> None:
        pl = PatentLogger(log_dir=str(tmp_path))
        pl.log_moment_detection("M01", True, 0.80, 0.12, 0.92, {"webcam": True})
        pl.log_eeg_quality_decision(0.85, 0.60, "use")

        with open(pl.log_file) as f:
            lines = f.readlines()

        assert len(lines) == 2
        for line in lines:
            record = json.loads(line)
            assert "timestamp" in record
            assert "datetime" in record

    def test_records_persist_across_writes(self, tmp_path: Path) -> None:
        pl = PatentLogger(log_dir=str(tmp_path))
        for i in range(5):
            pl.log_moment_detection(f"M{i:02d}", True, 0.80, 0.0, 0.80, {})

        assert len(pl.query_logs()) == 5


import json
