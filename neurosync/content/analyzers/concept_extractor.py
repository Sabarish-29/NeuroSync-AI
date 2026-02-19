"""
NeuroSync AI — Concept Extractor.

Uses GPT-4 to extract key concepts, learning objectives, and
prerequisite relationships from parsed document text.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger


@dataclass
class ExtractedConcept:
    """A single concept extracted from content."""
    concept_id: str
    name: str
    description: str
    difficulty: str = "medium"             # easy, medium, hard
    prerequisites: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    source_chunk_index: int = 0


@dataclass
class ConceptMap:
    """Full concept extraction result."""
    title: str
    summary: str
    concepts: list[ExtractedConcept] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    total_chunks_processed: int = 0
    raw_responses: list[dict[str, Any]] = field(default_factory=list)


class ConceptExtractor:
    """Extract concepts from text chunks using GPT-4."""

    SYSTEM_PROMPT = (
        "You are an expert educational content analyzer. Extract key concepts "
        "from the provided text. Return valid JSON with this structure:\n"
        '{"concepts": [{"concept_id": "c1", "name": "...", "description": "...", '
        '"difficulty": "easy|medium|hard", "prerequisites": [], "keywords": []}], '
        '"learning_objectives": ["..."], "summary": "..."}\n'
        "Extract 3-15 concepts per chunk. Be precise and educational."
    )

    def __init__(self, client: Any = None, model: str = "gpt-4-turbo-preview",
                 max_tokens: int = 2000, temperature: float = 0.3) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def extract_from_chunks(self, chunks: list[str], title: str = "") -> ConceptMap:
        """
        Extract concepts from multiple text chunks.

        Args:
            chunks: List of text chunks from the document.
            title: Document title for context.

        Returns:
            ConceptMap with all extracted concepts.
        """
        if not chunks:
            return ConceptMap(title=title or "Empty Document", summary="No content to analyze.")

        all_concepts: list[ExtractedConcept] = []
        all_objectives: list[str] = []
        raw_responses: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for i, chunk in enumerate(chunks):
            try:
                result = await self._extract_single_chunk(chunk, i, title)
                raw_responses.append(result)

                for c_data in result.get("concepts", []):
                    name = c_data.get("name", "").strip()
                    if name and name.lower() not in seen_names:
                        seen_names.add(name.lower())
                        concept = ExtractedConcept(
                            concept_id=c_data.get("concept_id", f"c{len(all_concepts)+1}"),
                            name=name,
                            description=c_data.get("description", ""),
                            difficulty=c_data.get("difficulty", "medium"),
                            prerequisites=c_data.get("prerequisites", []),
                            keywords=c_data.get("keywords", []),
                            source_chunk_index=i,
                        )
                        all_concepts.append(concept)

                for obj in result.get("learning_objectives", []):
                    if obj and obj not in all_objectives:
                        all_objectives.append(obj)

            except Exception as e:
                logger.warning("Concept extraction failed for chunk {}: {}", i, e)

        summary = raw_responses[0].get("summary", "") if raw_responses else ""

        logger.info(
            "Extracted {} concepts, {} objectives from {} chunks",
            len(all_concepts), len(all_objectives), len(chunks),
        )

        return ConceptMap(
            title=title or "Untitled",
            summary=summary,
            concepts=all_concepts,
            learning_objectives=all_objectives,
            total_chunks_processed=len(chunks),
            raw_responses=raw_responses,
        )

    async def _extract_single_chunk(self, chunk: str, index: int,
                                     title: str) -> dict[str, Any]:
        """Call GPT-4 to extract concepts from a single chunk."""
        if self.client is None:
            raise RuntimeError("OpenAI client not configured")

        user_msg = f"Document: {title}\nChunk {index + 1}:\n\n{chunk}"

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

        content = response.choices[0].message.content or "{}"
        return json.loads(content)
