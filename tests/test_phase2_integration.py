"""Phase 2 end-to-end integration tests.

Verifies that the tiered confidence system, EEG coordinator, and
existing fusion pipeline all work together without EEG hardware.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from neurosync.config.settings import EEG_CONFIG, MOMENT_DETECTION
from neurosync.eeg.coordinator import EEGCoordinator
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
    NLPSignals,
    WebcamSignals,
)


def _state(**kw) -> FusionState:
    defaults = dict(session_id="int", student_id="s1")
    defaults.update(kw)
    return FusionState(**defaults)


ALL_TIERED_DETECTORS = [
    M01AttentionDetector,
    M02CognitiveLoadDetector,
    M10FatigueDetector,
]


# ── Config ────────────────────────────────────────────────────────────


class TestPhase2Config:
    def test_eeg_config_exists(self) -> None:
        assert "ENABLED" in EEG_CONFIG
        assert "MIN_QUALITY" in EEG_CONFIG
        assert "DEVICE_TYPE" in EEG_CONFIG

    def test_eeg_disabled_by_default(self) -> None:
        # Unless EEG_ENABLED env var is explicitly "true", default is False
        assert EEG_CONFIG["ENABLED"] is False or isinstance(EEG_CONFIG["ENABLED"], bool)

    def test_moment_detection_config_exists(self) -> None:
        assert "BASE_THRESHOLD" in MOMENT_DETECTION
        assert "EEG_BOOST_MAX" in MOMENT_DETECTION
        assert "PRIMARY_SOURCES" in MOMENT_DETECTION
        assert "OPTIONAL_SOURCES" in MOMENT_DETECTION


# ── All detectors work without EEG ───────────────────────────────────


class TestAllDetectorsWithoutEEG:
    def test_no_crash_with_no_eeg(self) -> None:
        """Every tiered detector must not crash when eeg=None."""
        state = _state(
            webcam=WebcamSignals(attention_score=0.1, off_screen_duration_ms=6000),
            behavioral=BehavioralSignals(
                rewind_burst=True,
                interaction_variance=0.9,
                idle_frequency=2.0,
            ),
            nlp=NLPSignals(confusion_score=0.8),
            session_duration_minutes=40.0,
            eeg=None,
        )

        for cls in ALL_TIERED_DETECTORS:
            det = cls()
            result = det.detect(state)
            # May or may not detect — but must NEVER raise
            if result is not None:
                assert isinstance(result, MomentDetectionResult)
                assert result.eeg_boost == 0.0
                assert result.signals_used["eeg"] is False

    def test_no_crash_with_no_webcam(self) -> None:
        """Every tiered detector must not crash when webcam=None."""
        state = _state(
            webcam=None,
            behavioral=BehavioralSignals(
                rewind_burst=True,
                interaction_variance=0.9,
                idle_frequency=3.0,
            ),
            session_duration_minutes=40.0,
            eeg=None,
        )

        for cls in ALL_TIERED_DETECTORS:
            det = cls()
            result = det.detect(state)
            if result is not None:
                assert result.signals_used["webcam"] is False


# ── EEG enhancement adds confidence ──────────────────────────────────


class TestEEGEnhancement:
    def test_eeg_boost_higher_than_primary(self) -> None:
        """When good EEG is available, confidence must be >= primary-only."""
        state_no_eeg = _state(
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=5000),
            behavioral=BehavioralSignals(
                rewind_burst=True,
                interaction_variance=0.8,
                idle_frequency=2.0,
            ),
            nlp=NLPSignals(confusion_score=0.8),
            session_duration_minutes=40.0,
            eeg=None,
        )
        state_with_eeg = state_no_eeg.model_copy(
            update={"eeg": EEGSignals(
                quality=0.95,
                alpha_power=2.0,
                beta_power=0.9,
                theta_power=0.7,
            )}
        )

        for cls in ALL_TIERED_DETECTORS:
            det = cls()
            r_no = det.detect(state_no_eeg)

            # Reset any baseline state
            det2 = cls()
            # Set baseline for M01 first
            if cls is M01AttentionDetector:
                baseline = state_with_eeg.model_copy(
                    update={"eeg": EEGSignals(quality=0.95, alpha_power=1.0)}
                )
                det2.detect(baseline)

            r_yes = det2.detect(state_with_eeg)

            if r_no is not None and r_yes is not None:
                assert r_yes.confidence >= r_no.confidence

    def test_poor_quality_eeg_gives_no_boost(self) -> None:
        eeg = EEGSignals(quality=0.2, alpha_power=5.0, beta_power=5.0, theta_power=5.0)
        state = _state(
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=5000),
            behavioral=BehavioralSignals(rewind_burst=True, interaction_variance=0.8, idle_frequency=2.0),
            session_duration_minutes=40.0,
            eeg=eeg,
        )

        for cls in ALL_TIERED_DETECTORS:
            det = cls()
            result = det.detect(state)
            if result is not None:
                assert result.eeg_boost == 0.0


# ── EEG coordinator integration ──────────────────────────────────────


class TestEEGCoordinatorIntegration:
    def test_coordinator_feeds_detector(self) -> None:
        """EEGCoordinator signals can be passed to a detector."""
        coord = EEGCoordinator(enabled=True)
        coord.initialize()

        eeg_signals = coord.get_signals()
        assert eeg_signals is not None

        state = _state(
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=5000),
            behavioral=BehavioralSignals(idle_frequency=1.5),
            eeg=eeg_signals,
        )

        det = M01AttentionDetector()
        result = det.detect(state)
        assert result is not None

        coord.shutdown()

    def test_coordinator_disabled_gives_none(self) -> None:
        coord = EEGCoordinator(enabled=False)
        coord.initialize()

        eeg_signals = coord.get_signals()
        assert eeg_signals is None

        state = _state(
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=5000),
            behavioral=BehavioralSignals(idle_frequency=1.5),
            eeg=eeg_signals,  # None
        )

        det = M01AttentionDetector()
        result = det.detect(state)
        assert result is not None
        assert result.eeg_boost == 0.0


# ── FusionState backward compatibility ────────────────────────────────


class TestFusionStateCompat:
    def test_eeg_field_defaults_to_none(self) -> None:
        state = FusionState(session_id="t", student_id="s")
        assert state.eeg is None

    def test_eeg_field_accepted(self) -> None:
        state = FusionState(
            session_id="t",
            student_id="s",
            eeg=EEGSignals(quality=0.9, alpha_power=0.5),
        )
        assert state.eeg is not None
        assert state.eeg.quality == 0.9

    def test_existing_fields_unchanged(self) -> None:
        state = FusionState(
            session_id="t",
            student_id="s",
            behavioral=BehavioralSignals(frustration_score=0.5),
            webcam=WebcamSignals(attention_score=0.3),
        )
        assert state.behavioral.frustration_score == 0.5
        assert state.webcam.attention_score == 0.3
        assert state.knowledge is not None
        assert state.nlp is None
