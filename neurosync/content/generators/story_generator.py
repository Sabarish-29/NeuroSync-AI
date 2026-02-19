"""
NeuroSync AI — Story Generator.

Uses GPT-4 to generate story-based explanations of concepts.
Creates narrative-driven learning content that makes abstract
concepts relatable through analogies and storytelling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class StorySegment:
    """A segment of the educational story."""
    concept_name: str
    story_text: str
    analogy: str = ""
    moral: str = ""
    word_count: int = 0

    def __post_init__(self) -> None:
        self.word_count = len(self.story_text.split()) if self.story_text else 0


@dataclass
class FullStory:
    """Complete story-based explanation."""
    title: str
    introduction: str = ""
    segments: list[StorySegment] = field(default_factory=list)
    conclusion: str = ""
    total_word_count: int = 0

    def full_text(self) -> str:
        """Return the complete story as a single text."""
        parts = [self.introduction]
        for seg in self.segments:
            parts.append(seg.story_text)
        parts.append(self.conclusion)
        return "\n\n".join(p for p in parts if p)

    def __post_init__(self) -> None:
        self.total_word_count = len(self.full_text().split())


class StoryGenerator:
    """Generate story-based explanations using GPT-4."""

    SYSTEM_PROMPT = (
        "You are a master storyteller and educator. Create an engaging story "
        "that explains the given concept through narrative and analogy. "
        "The story should:\n"
        "- Use relatable characters or scenarios\n"
        "- Build understanding step by step through the narrative\n"
        "- Include a clear analogy that maps to the concept\n"
        "- End with a takeaway that reinforces the learning\n"
        "Return valid JSON: {\"story\": \"...\", \"analogy\": \"...\", \"moral\": \"...\"}"
    )

    def __init__(self, client: Any = None, model: str = "gpt-4-turbo-preview",
                 max_tokens: int = 2000, temperature: float = 0.8) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def generate_story(self, concepts: list[Any],
                              title: str = "") -> FullStory:
        """
        Generate a story-based explanation for the given concepts.

        Args:
            concepts: List of ExtractedConcept objects.
            title: Topic title.

        Returns:
            FullStory with narrative segments.
        """
        if not concepts:
            return FullStory(title=title or "Empty Story")

        segments: list[StorySegment] = []

        # Introduction
        concept_names = [c.name for c in concepts[:5]]
        intro = (
            f"Imagine you're about to discover the secrets behind "
            f"{', '.join(concept_names)}. Let's embark on this journey together."
        )

        # Generate story for each concept
        for concept in concepts:
            try:
                segment = await self._generate_segment(concept, title)
                segments.append(segment)
            except Exception as e:
                logger.warning("Story generation failed for {}: {}", concept.name, e)
                # Fallback
                segments.append(StorySegment(
                    concept_name=concept.name,
                    story_text=(
                        f"Think of {concept.name} as something you encounter every day. "
                        f"{concept.description}. Once you understand this foundation, "
                        f"everything else starts to make sense."
                    ),
                    analogy=f"{concept.name} is like building blocks in a tower.",
                    moral=f"Understanding {concept.name} is key to mastering this topic.",
                ))

        # Conclusion
        conclusion = (
            f"And so our journey through {title or 'this topic'} comes to an end. "
            f"We explored {len(concepts)} fascinating concepts, each building on the last. "
            "Remember: the best way to learn is to connect new ideas to what you already know."
        )

        story = FullStory(
            title=title or "A Learning Story",
            introduction=intro,
            segments=segments,
            conclusion=conclusion,
        )

        logger.info(
            "Generated story: {} segments, {} words",
            len(segments), story.total_word_count,
        )
        return story

    async def _generate_segment(self, concept: Any, title: str) -> StorySegment:
        """Generate a story segment for one concept."""
        if self.client is None:
            raise RuntimeError("OpenAI client not configured")

        user_msg = (
            f"Topic: {title}\n"
            f"Concept: {concept.name}\n"
            f"Description: {concept.description}\n"
            f"Difficulty: {concept.difficulty}"
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or '{"story": ""}'
        data = json.loads(content)

        return StorySegment(
            concept_name=concept.name,
            story_text=data.get("story", concept.description or ""),
            analogy=data.get("analogy", ""),
            moral=data.get("moral", ""),
        )
