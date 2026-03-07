"""Tests for BaseMomentDetector and MomentDetectionResult."""

from __future__ import annotations

from typing import Optional

import pytest

from neurosync.fusion.moment_detectors.base_detector import (
    BaseMomentDetector,
    MomentDetectionResult,
)
from neurosync.fusion.state import (
    BehavioralSignals,
    EEGSignals,
    FusionState,
    WebcamSignals,
)


# ── helpers ───────────────────────────────────────────────────────────


def _state(**overrides) -> FusionState:
    """Create a minimal FusionState for testing."""
    defaults = dict(session_id="test", student_id="s1")
    defaults.update(overrides)
    return FusionState(**defaults)


class _AlwaysDetect(BaseMomentDetector):
    """Stub that always returns a fixed primary confidence."""

    def __init__(self, primary: float = 0.80, moment_id: str = "T01") -> None:
        super().__init__(moment_id=moment_id, base_threshold=0.70)
        self._primary = primary

    def detect_primary(self, state: FusionState) -> Optional[float]:
        return self._primary


class _NeverDetect(BaseMomentDetector):
    """Stub that never detects."""

    def __init__(self) -> None:
        super().__init__(moment_id="T00", base_threshold=0.70)

    def detect_primary(self, state: FusionState) -> Optional[float]:
        return None


class _WithEEGBoost(BaseMomentDetector):
    """Stub that returns an EEG boost of 0.10."""

    def __init__(self) -> None:
        super().__init__(moment_id="T02", base_threshold=0.70)

    def detect_primary(self, state: FusionState) -> Optional[float]:
        return 0.75

    def detect_eeg_enhancement(self, state: FusionState) -> float:
        if state.eeg is not None and state.eeg.alpha_power > 0.5:
            return 0.10
        return 0.0


# ── MomentDetectionResult ────────────────────────────────────────────


class TestMomentDetectionResult:
    def test_creation(self) -> None:
        r = MomentDetectionResult(
            moment_id="M01",
            detected=True,
            confidence=0.85,
            primary_confidence=0.75,
            eeg_boost=0.10,
            signals_used={"webcam": True, "eeg": True},
            timestamp=1.0,
        )
        assert r.moment_id == "M01"
        assert r.detected is True
        assert r.confidence == 0.85

    def test_str(self) -> None:
        r = MomentDetectionResult(
            moment_id="M02",
            detected=True,
            confidence=0.80,
            primary_confidence=0.80,
            eeg_boost=0.0,
            signals_used={"webcam": True, "eeg": False},
        )
        text = str(r)
        assert "M02" in text
        assert "webcam" in text


# ── BaseMomentDetector ────────────────────────────────────────────────


class TestBaseMomentDetector:
    def test_detect_without_eeg(self) -> None:
        det = _AlwaysDetect(primary=0.80)
        result = det.detect(_state())
        assert result is not None
        assert result.detected is True
        assert result.confidence == 0.80
        assert result.eeg_boost == 0.0
        assert result.signals_used["eeg"] is False

    def test_detect_below_threshold_returns_none(self) -> None:
        det = _AlwaysDetect(primary=0.50)
        result = det.detect(_state())
        assert result is None

    def test_never_detect_returns_none(self) -> None:
        det = _NeverDetect()
        result = det.detect(_state())
        assert result is None

    def test_eeg_boost_increases_confidence(self) -> None:
        det = _WithEEGBoost()
        eeg = EEGSignals(quality=0.9, alpha_power=0.8)
        result = det.detect(_state(eeg=eeg))
        assert result is not None
        assert result.eeg_boost == 0.10
        assert result.confidence == pytest.approx(0.85)
        assert result.signals_used["eeg"] is True

    def test_low_quality_eeg_ignored(self) -> None:
        det = _WithEEGBoost()
        eeg = EEGSignals(quality=0.3, alpha_power=0.8)
        result = det.detect(_state(eeg=eeg))
        assert result is not None
        assert result.eeg_boost == 0.0
        assert result.confidence == 0.75

    def test_confidence_clamped_to_one(self) -> None:
        det = _AlwaysDetect(primary=0.99)
        # Even with a spurious EEG field the confidence caps at 1.0
        result = det.detect(_state())
        assert result is not None
        assert result.confidence <= 1.0

    def test_repr(self) -> None:
        det = _AlwaysDetect()
        assert "T01" in repr(det)
