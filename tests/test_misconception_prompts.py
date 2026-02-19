"""
Tests for MisconceptionPrompts (Step 6) — 2 tests.
"""

from neurosync.interventions.prompts.misconception import MisconceptionPrompts


def test_misconception_prompt_non_judgmental():
    """Build prompt → contains 'common misconception' framing."""
    ctx = {
        "concept_name": "photosynthesis",
        "wrong_answer": "plants eat from soil",
        "correct_answer": "plants make food from sunlight",
        "grade_level": 8,
    }
    prompt = MisconceptionPrompts.build(ctx)
    assert "common misconception" in prompt.lower()
    assert "non-judgmental" in prompt.lower() or "Non-judgmental" in prompt


def test_misconception_includes_both_answers():
    """Build prompt → contains both wrong and correct answer."""
    ctx = {
        "concept_name": "gravity",
        "wrong_answer": "heavier objects fall faster",
        "correct_answer": "all objects fall at the same rate in a vacuum",
        "grade_level": 9,
    }
    prompt = MisconceptionPrompts.build(ctx)
    assert "heavier objects fall faster" in prompt
    assert "all objects fall at the same rate in a vacuum" in prompt
