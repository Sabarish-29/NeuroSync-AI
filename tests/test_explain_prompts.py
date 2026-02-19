"""
Tests for ExplainPrompts (Step 6) — 3 tests.
"""

from neurosync.interventions.prompts.explain import ExplainPrompts


def test_explain_prompt_includes_prerequisites():
    """Missing prerequisites provided → prompt mentions them."""
    ctx = {
        "concept_name": "East India Company",
        "lesson_topic": "British colonialism",
        "grade_level": 10,
        "missing_prerequisites": ["mercantilism", "colonial trade"],
    }
    prompt = ExplainPrompts.build(ctx)
    assert "East India Company" in prompt
    assert "mercantilism" in prompt
    assert "colonial trade" in prompt
    assert "grade 10" in prompt


def test_explain_validates_length_40_60_words():
    """Response 45 words → accepted as-is."""
    text = " ".join(["word"] * 45) + "."
    result = ExplainPrompts.validate_length(text)
    assert result == text  # no modification


def test_explain_truncates_long_response():
    """Response 85 words → truncated near 60 at sentence boundary."""
    # Build a response with clear sentence boundary at word ~55
    part1 = " ".join(["word"] * 54) + "."
    part2 = " ".join(["extra"] * 30) + "."
    long_text = part1 + " " + part2
    result = ExplainPrompts.validate_length(long_text)
    assert len(result.split()) <= 65  # truncated near 60
