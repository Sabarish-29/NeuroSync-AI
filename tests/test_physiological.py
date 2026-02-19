"""Tests for the physiological (blink-rate) anxiety assessment (Step 9)."""

from neurosync.readiness.assessments.physiological import assess_blink_rate


class TestPhysiological:
    """Blink-rate assessment tests."""

    def test_normal_blink_rate(self) -> None:
        """Blink rate 15 bpm (normal range) → low anxiety ~0.30."""
        result = assess_blink_rate(15.0)
        assert result.available is True
        assert result.anxiety_score == 0.30

    def test_high_blink_rate(self) -> None:
        """Blink rate 35 bpm (elevated) → high anxiety > 0.7."""
        result = assess_blink_rate(35.0)
        assert result.available is True
        assert result.anxiety_score > 0.7

    def test_unavailable(self) -> None:
        """None blink rate → fallback 0.50, available=False."""
        result = assess_blink_rate(None)
        assert result.available is False
        assert result.anxiety_score == 0.50
