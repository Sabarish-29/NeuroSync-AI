"""
Tests for PlateauPrompts (Step 6) — 2 tests.
"""

from neurosync.interventions.prompts.plateau import PlateauPrompts


def test_plateau_prompt_includes_failed_methods():
    """Failed methods=['video', 'diagram'] → prompt lists them."""
    ctx = {
        "concept_name": "osmosis",
        "concept_definition": "Movement of water through a semipermeable membrane.",
        "failed_methods": ["video", "diagram"],
        "new_method": "story_analogy",
        "grade_level": 8,
    }
    prompt = PlateauPrompts.build(ctx)
    assert "- video" in prompt
    assert "- diagram" in prompt


def test_plateau_prompt_uses_correct_method_instruction():
    """new_method='story_analogy' → prompt includes story instruction."""
    ctx = {
        "concept_name": "osmosis",
        "concept_definition": "Movement of water through a semipermeable membrane.",
        "failed_methods": ["lecture"],
        "new_method": "story_analogy",
        "grade_level": 8,
    }
    prompt = PlateauPrompts.build(ctx)
    expected = PlateauPrompts.METHOD_INSTRUCTIONS["story_analogy"]
    assert expected in prompt
