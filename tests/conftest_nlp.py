"""
NeuroSync AI — NLP test fixtures (Step 4).

Sample texts for sentiment, complexity, confusion, keyword, and quality tests.
"""

from __future__ import annotations

import pytest

from neurosync.core.events import TextEvent
from neurosync.nlp.pipeline import NLPPipeline


# =============================================================================
# Sample texts — sentiment
# =============================================================================

POSITIVE_TEXT = "I love learning about photosynthesis! It's really fascinating and I feel great about understanding it."
NEGATIVE_TEXT = "This is terrible. I hate this topic and nothing makes sense at all."
NEUTRAL_TEXT = "Photosynthesis is the process by which plants convert light energy into chemical energy."
FRUSTRATED_TEXT = "I absolutely hate this stupid lesson! Nothing works and I can't do anything right. This is awful and pointless."

# =============================================================================
# Sample texts — complexity
# =============================================================================

SIMPLE_TEXT = "The cat sat on the mat."
MODERATE_TEXT = "Photosynthesis is the process by which green plants use sunlight to synthesize nutrients from carbon dioxide and water."
COMPLEX_TEXT = (
    "The mitochondrial electron transport chain comprises four enzymatic complexes "
    "embedded in the inner mitochondrial membrane, facilitating oxidative phosphorylation "
    "through chemiosmotic coupling of proton gradients across the intermembrane space, "
    "ultimately generating adenosine triphosphate through the rotary catalysis mechanism "
    "of ATP synthase."
)

# =============================================================================
# Sample texts — confusion
# =============================================================================

CONFUSED_TEXT = "I'm not sure what this means? Maybe I don't understand? I guess I'm confused about the whole concept."
CLEAR_TEXT = "Photosynthesis converts carbon dioxide and water into glucose and oxygen using sunlight."
MILDLY_CONFUSED_TEXT = "I think this might be about energy conversion but I'm not completely certain."

# =============================================================================
# Sample texts — answer quality
# =============================================================================

SHORT_ANSWER = "yes"
MEDIUM_ANSWER = "Photosynthesis converts light energy into chemical energy in plants."
DETAILED_ANSWER = (
    "Photosynthesis is the process by which plants convert light energy from the sun "
    "into chemical energy stored in glucose. This occurs primarily in the chloroplasts, "
    "specifically in the thylakoid membranes. The process involves two main stages: "
    "the light-dependent reactions, which produce ATP and NADPH, and the Calvin cycle, "
    "which uses these products to fix carbon dioxide into glucose. Because this process "
    "releases oxygen as a byproduct, it is essential for life on Earth."
)

CONCEPT_KEYWORDS = ["photosynthesis", "light", "energy", "glucose", "chloroplast", "oxygen", "carbon"]

# =============================================================================
# Sample texts — topic drift
# =============================================================================

ON_TOPIC_TEXT = "Photosynthesis uses light energy to produce glucose and oxygen in the chloroplasts."
OFF_TOPIC_TEXT = "My favorite movie is about space exploration and astronauts on Mars."

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def nlp_pipeline() -> NLPPipeline:
    """Create a fresh NLP pipeline."""
    return NLPPipeline()


@pytest.fixture
def text_event() -> TextEvent:
    """Create a sample text event."""
    return TextEvent(
        session_id="test_session",
        student_id="test_student",
        text=MODERATE_TEXT,
        text_type="answer",
        concept_id="concept_1",
    )
