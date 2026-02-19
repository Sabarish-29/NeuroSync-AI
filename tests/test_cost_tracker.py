"""
Tests for CostTracker (Step 6) — 2 tests.
"""

from neurosync.interventions.cost_tracker import CostTracker


def test_cost_tracker_enforces_session_limit():
    """Session cost reaches limit → can_afford_request = False."""
    tracker = CostTracker(session_limit=0.01)
    # Record a request that costs more than the limit
    tracker.record_request(input_tokens=500, output_tokens=500, model="gpt-4-turbo-preview")
    assert not tracker.can_afford_request()


def test_cost_tracker_calculates_cost_correctly():
    """100 input + 50 output tokens → cost matches pricing formula."""
    tracker = CostTracker()
    cost = tracker.record_request(
        input_tokens=100,
        output_tokens=50,
        model="gpt-4-turbo-preview",
    )
    # gpt-4-turbo-preview: input=$0.01/1K, output=$0.03/1K
    expected = 100 * (0.01 / 1000) + 50 * (0.03 / 1000)
    assert abs(cost - expected) < 1e-9
    assert tracker.session_requests == 1
    assert tracker.session_input_tokens == 100
    assert tracker.session_output_tokens == 50
