"""
Tests for RescuePrompts (Step 6) — 2 tests.
"""

from neurosync.interventions.prompts.rescue import RescuePrompts


def test_rescue_prompt_validates_difficulty():
    """High frustration score → prompt includes 'highly frustrated'."""
    ctx = {
        "concept_name": "quadratic equations",
        "frustration_score": 0.80,
        "failed_attempts": 5,
        "lesson_topic": "algebra",
        "grade_level": 9,
    }
    prompt = RescuePrompts.build(ctx)
    assert "highly" in prompt.lower()
    assert "quadratic equations" in prompt


def test_rescue_prompt_includes_attempt_count():
    """Failed 3 times → prompt mentions 'tried 3 times'."""
    ctx = {
        "concept_name": "osmosis",
        "frustration_score": 0.55,
        "failed_attempts": 3,
        "lesson_topic": "biology",
        "grade_level": 8,
    }
    prompt = RescuePrompts.build(ctx)
    assert "3 times" in prompt
