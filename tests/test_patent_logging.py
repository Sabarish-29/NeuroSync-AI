"""Tests for patent_logger.py — evidence trail logging."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from neurosync.utils.patent_logger import (
    PatentLogger,
    get_patent_logger,
    reset_patent_logger,
)


@pytest.fixture()
def tmp_logger(tmp_path: Path) -> PatentLogger:
    """Return a PatentLogger writing to a temporary directory."""
    return PatentLogger(log_dir=str(tmp_path))


# ── PatentLogger creation ──────────────────────────────────────────


class TestPatentLoggerInit:
    def test_creates_log_directory(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "new_dir"
        logger = PatentLogger(log_dir=str(log_dir))
        assert log_dir.exists()

    def test_log_file_has_date_in_name(self, tmp_logger: PatentLogger) -> None:
        assert "patent_evidence_" in tmp_logger.log_file.name
        assert tmp_logger.log_file.suffix == ".jsonl"


# ── Moment detection logging ──────────────────────────────────────


class TestMomentDetectionLogging:
    def test_log_moment_detection(self, tmp_logger: PatentLogger) -> None:
        tmp_logger.log_moment_detection(
            moment_id="M01",
            detected=True,
            primary_confidence=0.78,
            eeg_boost=0.12,
            total_confidence=0.90,
            signals_used={"webcam": True, "behavioral": True, "eeg": True},
        )

        records = tmp_logger.query_logs()
        assert len(records) == 1
        r = records[0]
        assert r["event"] == "moment_detection"
        assert r["moment_id"] == "M01"
        assert r["detected"] is True
        assert r["confidence"]["primary"] == 0.78
        assert r["confidence"]["eeg_boost"] == 0.12
        assert r["confidence"]["total"] == 0.90
        assert "timestamp" in r

    def test_log_detection_with_metadata(self, tmp_logger: PatentLogger) -> None:
        tmp_logger.log_moment_detection(
            moment_id="M02",
            detected=True,
            primary_confidence=0.75,
            eeg_boost=0.0,
            total_confidence=0.75,
            signals_used={"webcam": False, "behavioral": True},
            metadata={"threshold": 0.70},
        )

        records = tmp_logger.query_logs(moment_id="M02")
        assert len(records) == 1
        assert records[0]["metadata"]["threshold"] == 0.70


# ── EEG quality decision logging ──────────────────────────────────


class TestEEGQualityLogging:
    def test_log_eeg_use_decision(self, tmp_logger: PatentLogger) -> None:
        tmp_logger.log_eeg_quality_decision(
            quality_score=0.85,
            threshold=0.60,
            decision="use",
        )

        records = tmp_logger.query_logs(event_type="eeg_quality_decision")
        assert len(records) == 1
        assert records[0]["decision"] == "use"
        assert records[0]["quality"] == 0.85

    def test_log_eeg_fallback_decision(self, tmp_logger: PatentLogger) -> None:
        tmp_logger.log_eeg_quality_decision(
            quality_score=0.40,
            threshold=0.60,
            decision="fallback",
            reason="quality below threshold",
        )

        records = tmp_logger.query_logs(event_type="eeg_quality_decision")
        assert len(records) == 1
        assert records[0]["decision"] == "fallback"
        assert records[0]["reason"] == "quality below threshold"


# ── Threshold application logging ─────────────────────────────────


class TestThresholdLogging:
    def test_log_threshold_application(self, tmp_logger: PatentLogger) -> None:
        tmp_logger.log_threshold_application(
            detector_id="M01",
            threshold_name="WEBCAM_ATTENTION_THRESHOLD",
            threshold_value=0.30,
            measured_value=0.15,
            condition_met=True,
        )

        records = tmp_logger.query_logs(event_type="threshold_application")
        assert len(records) == 1
        assert records[0]["threshold_name"] == "WEBCAM_ATTENTION_THRESHOLD"
        assert records[0]["met"] is True


# ── Confidence fusion logging ─────────────────────────────────────


class TestConfidenceFusionLogging:
    def test_log_confidence_fusion(self, tmp_logger: PatentLogger) -> None:
        tmp_logger.log_confidence_fusion(
            moment_id="M01",
            primary_sources={"webcam": 0.54, "behavioral": 0.36},
            eeg_contribution=0.12,
            fusion_method="weighted_sum",
            final_confidence=0.90,
        )

        records = tmp_logger.query_logs(event_type="confidence_fusion")
        assert len(records) == 1
        assert records[0]["primary_sources"]["webcam"] == 0.54
        assert records[0]["method"] == "weighted_sum"


# ── Query filtering ───────────────────────────────────────────────


class TestQueryLogs:
    def test_filter_by_event_type(self, tmp_logger: PatentLogger) -> None:
        tmp_logger.log_moment_detection(
            "M01", True, 0.80, 0.0, 0.80, {"webcam": True}
        )
        tmp_logger.log_eeg_quality_decision(0.85, 0.60, "use")

        assert len(tmp_logger.query_logs(event_type="moment_detection")) == 1
        assert len(tmp_logger.query_logs(event_type="eeg_quality_decision")) == 1

    def test_filter_by_moment_id(self, tmp_logger: PatentLogger) -> None:
        tmp_logger.log_moment_detection(
            "M01", True, 0.80, 0.0, 0.80, {"webcam": True}
        )
        tmp_logger.log_moment_detection(
            "M02", True, 0.75, 0.0, 0.75, {"behavioral": True}
        )

        assert len(tmp_logger.query_logs(moment_id="M01")) == 1
        assert len(tmp_logger.query_logs(moment_id="M02")) == 1

    def test_limit_parameter(self, tmp_logger: PatentLogger) -> None:
        for i in range(10):
            tmp_logger.log_moment_detection(
                f"M{i:02d}", True, 0.80, 0.0, 0.80, {}
            )

        assert len(tmp_logger.query_logs(limit=3)) == 3

    def test_empty_log_returns_empty(self, tmp_logger: PatentLogger) -> None:
        assert tmp_logger.query_logs() == []


# ── Global singleton ──────────────────────────────────────────────


class TestGlobalSingleton:
    def test_get_patent_logger_returns_same_instance(self) -> None:
        reset_patent_logger()
        a = get_patent_logger()
        b = get_patent_logger()
        assert a is b
        reset_patent_logger()

    def test_reset_patent_logger(self) -> None:
        reset_patent_logger()
        a = get_patent_logger()
        reset_patent_logger()
        b = get_patent_logger()
        assert a is not b
        reset_patent_logger()
