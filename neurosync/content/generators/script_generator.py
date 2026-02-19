"""
NeuroSync AI — Script Generator.

Uses GPT-4 to generate narration scripts for each slide/concept.
Scripts are optimized for text-to-speech delivery.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class NarrationScript:
    """Script for narrating a single slide/concept."""
    concept_name: str
    script_text: str
    estimated_duration_seconds: float = 0.0
    word_count: int = 0

    def __post_init__(self) -> None:
        self.word_count = len(self.script_text.split()) if self.script_text else 0
        # ~150 words per minute for narration
        self.estimated_duration_seconds = self.word_count / 2.5 if self.word_count else 0.0


@dataclass
class FullScript:
    """Complete script for all concepts."""
    title: str
    scripts: list[NarrationScript] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    total_word_count: int = 0

    def __post_init__(self) -> None:
        self.total_word_count = sum(s.word_count for s in self.scripts)
        self.total_duration_seconds = sum(s.estimated_duration_seconds for s in self.scripts)


class ScriptGenerator:
    """Generate narration scripts using GPT-4."""

    SYSTEM_PROMPT = (
        "You are an expert educational narrator. Create a clear, engaging "
        "narration script for a learning video. The script should:\n"
        "- Be conversational and easy to follow when spoken aloud\n"
        "- Explain the concept step by step\n"
        "- Use simple transitions between ideas\n"
        "- Be 60-120 words per concept\n"
        "Return valid JSON: {\"script\": \"...\"}"
    )

    def __init__(self, client: Any = None, model: str = "gpt-4-turbo-preview",
                 max_tokens: int = 1500, temperature: float = 0.7) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def generate_scripts(self, concepts: list[Any],
                                title: str = "") -> FullScript:
        """
        Generate narration scripts for all concepts.

        Args:
            concepts: List of ExtractedConcept objects.
            title: Document/presentation title.

        Returns:
            FullScript with narration for each concept.
        """
        if not concepts:
            return FullScript(title=title or "Empty", scripts=[])

        scripts: list[NarrationScript] = []

        # Intro script
        concept_names = [c.name for c in concepts[:5]]
        intro_text = (
            f"Welcome to {title or 'this lesson'}. Today we'll explore "
            f"{', '.join(concept_names)}. Let's get started."
        )
        scripts.append(NarrationScript(concept_name="Introduction", script_text=intro_text))

        # Per-concept scripts
        for concept in concepts:
            try:
                script = await self._generate_single(concept, title)
                scripts.append(script)
            except Exception as e:
                logger.warning("Script generation failed for {}: {}", concept.name, e)
                # Fallback script
                fallback = (
                    f"Let's discuss {concept.name}. {concept.description}. "
                    f"This is a {concept.difficulty} level topic."
                )
                scripts.append(NarrationScript(
                    concept_name=concept.name,
                    script_text=fallback,
                ))

        # Outro script
        outro = (
            f"That concludes our lesson on {title or 'this topic'}. "
            f"We covered {len(concepts)} key concepts. "
            "Review the material and test your understanding with the quiz."
        )
        scripts.append(NarrationScript(concept_name="Conclusion", script_text=outro))

        full = FullScript(title=title or "Untitled", scripts=scripts)
        logger.info(
            "Generated {} scripts, ~{:.0f}s total duration",
            len(scripts), full.total_duration_seconds,
        )
        return full

    async def _generate_single(self, concept: Any, title: str) -> NarrationScript:
        """Generate a narration script for one concept."""
        if self.client is None:
            raise RuntimeError("OpenAI client not configured")

        user_msg = (
            f"Topic: {title}\n"
            f"Concept: {concept.name}\n"
            f"Description: {concept.description}\n"
            f"Difficulty: {concept.difficulty}\n"
            f"Keywords: {', '.join(concept.keywords) if concept.keywords else 'none'}"
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

        content = response.choices[0].message.content or '{"script": ""}'
        data = json.loads(content)
        script_text = data.get("script", concept.description or "")

        return NarrationScript(concept_name=concept.name, script_text=script_text)
