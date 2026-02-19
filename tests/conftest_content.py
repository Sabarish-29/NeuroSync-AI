"""
NeuroSync AI — Content generation test fixtures (Step 7).

Mock OpenAI API responses for concept extraction, scripts,
stories, quizzes, diagrams, and TTS so tests never call real APIs.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from neurosync.content.analyzers.concept_extractor import ConceptExtractor, ExtractedConcept
from neurosync.content.generators.quiz_generator import QuizGenerator
from neurosync.content.generators.script_generator import ScriptGenerator
from neurosync.content.generators.story_generator import StoryGenerator
from neurosync.content.generators.diagram_generator import DiagramGenerator
from neurosync.content.tts.openai_tts import OpenAITTS


# ── Helper: mock OpenAI chat response ──────────────────────────────


def _make_chat_response(content_dict: dict) -> MagicMock:
    """Build a mock OpenAI ChatCompletion response with JSON content."""
    msg = MagicMock()
    msg.content = json.dumps(content_dict)

    choice = MagicMock()
    choice.message = msg

    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50
    usage.total_tokens = 150

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def _make_image_response(url: str = "https://example.com/diagram.png") -> MagicMock:
    """Build a mock DALL-E image response."""
    data_item = MagicMock()
    data_item.url = url
    resp = MagicMock()
    resp.data = [data_item]
    return resp


def _make_tts_response(audio_bytes: bytes = b"fake-audio-mp3-content") -> MagicMock:
    """Build a mock TTS response."""
    resp = MagicMock()
    resp.content = audio_bytes
    return resp


# ── Sample concept extraction response ──────────────────────────


SAMPLE_CONCEPT_RESPONSE = {
    "concepts": [
        {
            "concept_id": "c1",
            "name": "Photosynthesis",
            "description": "The process by which plants convert light energy into chemical energy.",
            "difficulty": "medium",
            "prerequisites": [],
            "keywords": ["chlorophyll", "light", "glucose", "carbon dioxide"],
        },
        {
            "concept_id": "c2",
            "name": "Cellular Respiration",
            "description": "The metabolic process that converts nutrients into ATP energy.",
            "difficulty": "hard",
            "prerequisites": ["Photosynthesis"],
            "keywords": ["mitochondria", "ATP", "oxygen", "glucose"],
        },
    ],
    "learning_objectives": [
        "Understand the process of photosynthesis",
        "Explain the relationship between photosynthesis and cellular respiration",
    ],
    "summary": "An introduction to energy processes in living organisms.",
}

SAMPLE_SCRIPT_RESPONSE = {
    "script": (
        "Let's explore this fascinating concept together. "
        "Understanding this foundation will help you build "
        "deeper knowledge in biology."
    ),
}

SAMPLE_STORY_RESPONSE = {
    "story": (
        "Imagine a tiny factory inside every leaf. "
        "This factory takes sunlight and turns it into food. "
        "That's essentially what photosynthesis does."
    ),
    "analogy": "Photosynthesis is like a solar-powered food factory.",
    "moral": "Nature has been using solar energy long before we discovered it.",
}

SAMPLE_QUIZ_RESPONSE = {
    "questions": [
        {
            "question_id": "q1",
            "question_text": "What is the primary product of photosynthesis?",
            "question_type": "mcq",
            "difficulty": "easy",
            "options": ["Glucose", "Protein", "Fat", "Water"],
            "correct_answer": "Glucose",
            "explanation": "Photosynthesis produces glucose as its main product.",
            "points": 1,
        },
        {
            "question_id": "q2",
            "question_text": "Photosynthesis requires sunlight.",
            "question_type": "true_false",
            "difficulty": "easy",
            "options": ["True", "False"],
            "correct_answer": "True",
            "explanation": "Light energy is essential for photosynthesis.",
            "points": 1,
        },
        {
            "question_id": "q3",
            "question_text": "Explain the role of chlorophyll in photosynthesis.",
            "question_type": "short_answer",
            "difficulty": "medium",
            "options": [],
            "correct_answer": "Chlorophyll absorbs light energy to power photosynthesis.",
            "explanation": "Chlorophyll is the green pigment that captures light.",
            "points": 2,
        },
    ],
}


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def sample_concepts() -> list[ExtractedConcept]:
    """Pre-built concept list for generator tests."""
    return [
        ExtractedConcept(
            concept_id="c1",
            name="Photosynthesis",
            description="The process by which plants convert light energy into chemical energy.",
            difficulty="medium",
            prerequisites=[],
            keywords=["chlorophyll", "light", "glucose"],
        ),
        ExtractedConcept(
            concept_id="c2",
            name="Cellular Respiration",
            description="The metabolic process that converts nutrients into ATP energy.",
            difficulty="hard",
            prerequisites=["Photosynthesis"],
            keywords=["mitochondria", "ATP", "oxygen"],
        ),
    ]


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Fully mocked OpenAI client with chat, images, and audio."""
    client = MagicMock()

    # Chat completions (concepts, scripts, stories, quizzes)
    client.chat.completions.create = AsyncMock(
        return_value=_make_chat_response(SAMPLE_CONCEPT_RESPONSE),
    )

    # Image generation (DALL-E)
    client.images.generate = AsyncMock(
        return_value=_make_image_response(),
    )

    # Audio speech (TTS)
    client.audio.speech.create = AsyncMock(
        return_value=_make_tts_response(),
    )

    return client


@pytest.fixture
def concept_extractor(mock_openai_client) -> ConceptExtractor:
    """ConceptExtractor with mocked client."""
    return ConceptExtractor(client=mock_openai_client)


@pytest.fixture
def script_generator(mock_openai_client) -> ScriptGenerator:
    """ScriptGenerator with mocked client."""
    # Override to return script responses
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_chat_response(SAMPLE_SCRIPT_RESPONSE),
    )
    return ScriptGenerator(client=mock_openai_client)


@pytest.fixture
def story_generator(mock_openai_client) -> StoryGenerator:
    """StoryGenerator with mocked client."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_chat_response(SAMPLE_STORY_RESPONSE),
    )
    return StoryGenerator(client=mock_openai_client)


@pytest.fixture
def quiz_generator(mock_openai_client) -> QuizGenerator:
    """QuizGenerator with mocked client."""
    mock_openai_client.chat.completions.create = AsyncMock(
        return_value=_make_chat_response(SAMPLE_QUIZ_RESPONSE),
    )
    return QuizGenerator(client=mock_openai_client)


@pytest.fixture
def diagram_generator(mock_openai_client) -> DiagramGenerator:
    """DiagramGenerator with mocked DALL-E."""
    return DiagramGenerator(client=mock_openai_client)


@pytest.fixture
def tts_engine(mock_openai_client) -> OpenAITTS:
    """OpenAITTS with mocked speech API."""
    return OpenAITTS(client=mock_openai_client)
