"""
Tests for SimplifyPrompts (Step 6) — 3 tests.
"""

from neurosync.interventions.prompts.simplify import SimplifyPrompts


def test_simplify_prompt_includes_context():
    """Build prompt → contains original phrase and surrounding sentence."""
    ctx = {
        "original_phrase": "chlorophyll molecules in thylakoid membranes",
        "surrounding_sentence": "The chlorophyll molecules in thylakoid membranes absorb photons.",
        "subject": "biology",
        "grade_level": 8,
    }
    prompt = SimplifyPrompts.build(ctx)
    assert "chlorophyll molecules in thylakoid membranes" in prompt
    assert "grade 8" in prompt
    assert "biology" in prompt
    assert "Maximum 15 words" in prompt


def test_simplify_response_enforces_word_limit():
    """Response > 15 words → truncated to 15."""
    long_response = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen"
    cleaned = SimplifyPrompts.parse_response(long_response)
    assert len(cleaned.split()) <= 16  # 15 words + possible "..."


def test_simplify_removes_quotes():
    """Response has quotes → cleaned response without quotes."""
    assert SimplifyPrompts.parse_response('"the green parts in cells"') == "the green parts in cells"
    assert SimplifyPrompts.parse_response("'energy makers'") == "energy makers"
