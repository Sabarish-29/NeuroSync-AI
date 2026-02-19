"""Tests for the readiness scorer (Step 9)."""

from neurosync.readiness.scorer import compute


class TestScorer:
    """Readiness scorer tests."""

    def test_all_low_anxiety(self) -> None:
        """All components low → high readiness, status 'ready'."""
        result = compute(
            self_report_anxiety=0.1,
            physiological_anxiety=0.2,
            behavioral_anxiety=0.1,
        )
        assert result.readiness > 0.8
        assert result.status == "ready"

    def test_webcam_unavailable_redistributes_weights(self) -> None:
        """When webcam unavailable, physiological weight is redistributed."""
        with_cam = compute(0.5, 0.5, 0.5, webcam_available=True)
        without_cam = compute(0.5, 0.5, 0.5, webcam_available=False)
        # Both should give same combined anxiety since all inputs are 0.5
        assert abs(with_cam.combined_anxiety - 0.5) < 0.01
        assert abs(without_cam.combined_anxiety - 0.5) < 0.01

    def test_ready_threshold(self) -> None:
        """Readiness >= 0.60 should yield status 'ready'."""
        # anxiety 0.35 → readiness 0.65 → ready
        result = compute(0.35, 0.35, 0.35, webcam_available=True)
        assert result.readiness >= 0.60
        assert result.status == "ready"

    def test_not_ready_recommendation(self) -> None:
        """High anxiety → not ready or needs_intervention."""
        result = compute(0.9, 0.9, 0.9, webcam_available=True)
        assert result.status in ("not_ready", "needs_intervention")
        assert result.readiness < 0.60
