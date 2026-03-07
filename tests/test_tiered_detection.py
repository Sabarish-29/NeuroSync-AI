"""Tests for the three tiered moment detectors (M01, M02, M10)."""

from __future__ import annotations

import pytest

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
    defaults = dict(session_id="t", student_id="s")
    defaults.update(kw)
    return FusionState(**defaults)


# ── M01 Attention ─────────────────────────────────────────────────────


class TestM01Attention:
    def test_no_detection_when_attentive(self) -> None:
        det = M01AttentionDetector()
        state = _state(webcam=WebcamSignals(attention_score=0.9))
        assert det.detect(state) is None

    def test_detection_on_low_attention(self) -> None:
        det = M01AttentionDetector()
        state = _state(
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=5000),
            behavioral=BehavioralSignals(idle_frequency=1.5),
        )
        result = det.detect(state)
        assert result is not None
        assert result.moment_id == "M01"
        assert result.eeg_boost == 0.0

    def test_detection_behavioral_only(self) -> None:
        """Works even when webcam is None (behavioral-only)."""
        det = M01AttentionDetector()
        state = _state(
            webcam=None,
            behavioral=BehavioralSignals(idle_frequency=2.0),
        )
        result = det.detect(state)
        # idle_frequency=2.0 -> idle_ms=120000 -> score=1.0, above threshold
        assert result is not None
        assert result.signals_used["webcam"] is False

    def test_eeg_boost_adds_confidence(self) -> None:
        det = M01AttentionDetector()
        # First call sets the baseline
        baseline_state = _state(
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=4000),
            behavioral=BehavioralSignals(idle_frequency=1.5),
            eeg=EEGSignals(quality=0.9, alpha_power=1.0),
        )
        det.detect(baseline_state)

        # Second call with elevated alpha
        elevated_state = _state(
            webcam=WebcamSignals(attention_score=0.10, off_screen_duration_ms=4000),
            behavioral=BehavioralSignals(idle_frequency=1.5),
            eeg=EEGSignals(quality=0.9, alpha_power=2.0),
        )
        result = det.detect(elevated_state)
        assert result is not None
        assert result.eeg_boost == pytest.approx(0.12)


# ── M02 Cognitive Load ────────────────────────────────────────────────


class TestM02CognitiveLoad:
    def test_no_detection_when_calm(self) -> None:
        det = M02CognitiveLoadDetector()
        state = _state(behavioral=BehavioralSignals(rewind_burst=False))
        assert det.detect(state) is None

    def test_detection_on_rewind_burst(self) -> None:
        det = M02CognitiveLoadDetector()
        state = _state(
            behavioral=BehavioralSignals(rewind_burst=True),
            webcam=WebcamSignals(frustration_boost=0.7),
        )
        result = det.detect(state)
        assert result is not None
        assert result.moment_id == "M02"

    def test_detection_with_nlp_confusion(self) -> None:
        det = M02CognitiveLoadDetector()
        state = _state(
            behavioral=BehavioralSignals(rewind_burst=True),
            nlp=NLPSignals(confusion_score=0.8),
        )
        result = det.detect(state)
        assert result is not None
        assert result.confidence >= 0.70

    def test_eeg_beta_alpha_boost(self) -> None:
        det = M02CognitiveLoadDetector()
        state = _state(
            behavioral=BehavioralSignals(rewind_burst=True),
            webcam=WebcamSignals(frustration_boost=0.7),
            eeg=EEGSignals(quality=0.9, beta_power=0.9, alpha_power=0.5),
        )
        result = det.detect(state)
        assert result is not None
        assert result.eeg_boost == pytest.approx(0.15)


# ── M10 Fatigue ───────────────────────────────────────────────────────


class TestM10Fatigue:
    def test_no_detection_when_fresh(self) -> None:
        det = M10FatigueDetector()
        state = _state(
            behavioral=BehavioralSignals(interaction_variance=0.1),
            session_duration_minutes=5.0,
        )
        assert det.detect(state) is None

    def test_detection_high_variance_long_session(self) -> None:
        det = M10FatigueDetector()
        state = _state(
            behavioral=BehavioralSignals(interaction_variance=0.8, idle_frequency=2.0),
            session_duration_minutes=40.0,
        )
        result = det.detect(state)
        assert result is not None
        assert result.moment_id == "M10"

    def test_eeg_theta_boost(self) -> None:
        det = M10FatigueDetector()
        state = _state(
            behavioral=BehavioralSignals(interaction_variance=0.8, idle_frequency=2.0),
            session_duration_minutes=40.0,
            eeg=EEGSignals(quality=0.9, theta_power=0.7),
        )
        result = det.detect(state)
        assert result is not None
        assert result.eeg_boost == pytest.approx(0.12)

    def test_works_without_webcam(self) -> None:
        """Fatigue uses behavioral only — webcam not needed."""
        det = M10FatigueDetector()
        state = _state(
            webcam=None,
            behavioral=BehavioralSignals(interaction_variance=0.9, idle_frequency=3.0),
            session_duration_minutes=40.0,
        )
        result = det.detect(state)
        assert result is not None
        assert result.signals_used["webcam"] is False
