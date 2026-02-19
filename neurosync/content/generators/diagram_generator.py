"""
NeuroSync AI — Diagram Generator.

Uses DALL-E 3 to generate educational diagrams and illustrations
for concepts that benefit from visual representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from loguru import logger


@dataclass
class GeneratedDiagram:
    """A generated diagram/image for a concept."""
    concept_name: str
    prompt_used: str
    image_url: str = ""
    image_bytes: Optional[bytes] = None
    image_path: Optional[str] = None
    width: int = 1024
    height: int = 1024


class DiagramGenerator:
    """Generate educational diagrams using DALL-E 3."""

    PROMPT_TEMPLATE = (
        "Create a clear, educational diagram illustrating the concept of '{concept}'. "
        "Style: clean, professional, suitable for academic presentation. "
        "Include labels and arrows where appropriate. "
        "Context: {description}. "
        "The diagram should be easy to understand for {audience} students."
    )

    def __init__(self, client: Any = None, model: str = "dall-e-3",
                 size: str = "1024x1024", quality: str = "standard") -> None:
        self.client = client
        self.model = model
        self.size = size
        self.quality = quality

    async def generate_diagram(self, concept_name: str, description: str,
                                audience: str = "undergraduate") -> GeneratedDiagram:
        """
        Generate a single diagram for a concept.

        Args:
            concept_name: Name of the concept.
            description: Description for context.
            audience: Target audience level.

        Returns:
            GeneratedDiagram with URL/bytes.
        """
        prompt = self.PROMPT_TEMPLATE.format(
            concept=concept_name,
            description=description[:500],
            audience=audience,
        )

        if self.client is None:
            raise RuntimeError("OpenAI client not configured")

        response = await self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=self.size,
            quality=self.quality,
            n=1,
        )

        image_url = response.data[0].url if response.data else ""

        logger.info("Generated diagram for concept: {}", concept_name)

        return GeneratedDiagram(
            concept_name=concept_name,
            prompt_used=prompt,
            image_url=image_url,
        )

    async def generate_for_concepts(self, concepts: list[Any],
                                     audience: str = "undergraduate",
                                     max_diagrams: int = 5) -> list[GeneratedDiagram]:
        """
        Generate diagrams for hard/expert concepts.

        Only generates for concepts that would benefit from visualization.
        """
        diagrams: list[GeneratedDiagram] = []

        # Prioritize complex concepts
        complex_concepts = [
            c for c in concepts
            if getattr(c, "difficulty", "medium") in ("hard", "expert")
        ][:max_diagrams]

        # Fill remaining slots with other concepts
        if len(complex_concepts) < max_diagrams:
            remaining = [c for c in concepts if c not in complex_concepts]
            complex_concepts.extend(remaining[: max_diagrams - len(complex_concepts)])

        for concept in complex_concepts:
            try:
                diagram = await self.generate_diagram(
                    concept_name=concept.name,
                    description=getattr(concept, "description", ""),
                    audience=audience,
                )
                diagrams.append(diagram)
            except Exception as e:
                logger.warning("Diagram generation failed for {}: {}", concept.name, e)

        logger.info("Generated {} diagrams for {} concepts", len(diagrams), len(concepts))
        return diagrams
