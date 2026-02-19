"""
NeuroSync AI — Structure Analyzer.

Analyzes document structure: detects sections, headings, hierarchy,
and logical flow to inform content generation order.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Section:
    """A detected section in the document."""
    title: str
    level: int                           # 1 = chapter, 2 = section, 3 = subsection
    text: str
    start_index: int
    word_count: int = 0
    subsections: list["Section"] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.word_count = len(self.text.split()) if self.text.strip() else 0


@dataclass
class DocumentStructure:
    """Analyzed structure of the document."""
    title: str
    sections: list[Section] = field(default_factory=list)
    total_sections: int = 0
    max_depth: int = 0
    estimated_reading_minutes: int = 0


class StructureAnalyzer:
    """Detect and analyze document structure from text."""

    # Heading patterns (in order of specificity)
    HEADING_PATTERNS = [
        (1, re.compile(r"^(?:Chapter|CHAPTER)\s+\d+[.:]\s*(.+)$", re.MULTILINE)),
        (1, re.compile(r"^#{1}\s+(.+)$", re.MULTILINE)),           # Markdown H1
        (2, re.compile(r"^#{2}\s+(.+)$", re.MULTILINE)),           # Markdown H2
        (3, re.compile(r"^#{3}\s+(.+)$", re.MULTILINE)),           # Markdown H3
        (2, re.compile(r"^(\d+\.)\s+(.+)$", re.MULTILINE)),        # 1. Section
        (3, re.compile(r"^(\d+\.\d+)\s+(.+)$", re.MULTILINE)),    # 1.1 Subsection
        (1, re.compile(r"^([A-Z][A-Z\s]{5,})$", re.MULTILINE)),   # ALL CAPS heading
    ]

    WORDS_PER_MINUTE = 200  # average reading speed

    def analyze(self, text: str, title: str = "") -> DocumentStructure:
        """
        Analyze the structure of a document.

        Args:
            text: Full document text.
            title: Optional title override.

        Returns:
            DocumentStructure with detected sections and hierarchy.
        """
        if not text.strip():
            return DocumentStructure(title=title or "Empty")

        sections = self._detect_sections(text)
        max_depth = max((s.level for s in sections), default=0)
        word_count = len(text.split())
        reading_minutes = max(1, word_count // self.WORDS_PER_MINUTE)

        if not title and sections:
            title = sections[0].title

        return DocumentStructure(
            title=title or "Untitled",
            sections=sections,
            total_sections=len(sections),
            max_depth=max_depth,
            estimated_reading_minutes=reading_minutes,
        )

    def _detect_sections(self, text: str) -> list[Section]:
        """Detect sections by heading patterns."""
        # Collect all heading matches with positions
        headings: list[tuple[int, int, str]] = []  # (position, level, title)

        for level, pattern in self.HEADING_PATTERNS:
            for match in pattern.finditer(text):
                # Get the last group (the actual title text)
                title = match.group(match.lastindex or 0).strip()
                if len(title) > 2 and len(title) < 200:
                    headings.append((match.start(), level, title))

        # Sort by position
        headings.sort(key=lambda h: h[0])

        # Deduplicate overlapping matches (keep first at each position)
        deduped: list[tuple[int, int, str]] = []
        last_pos = -100
        for pos, level, title in headings:
            if pos > last_pos + 5:  # allow small gap
                deduped.append((pos, level, title))
                last_pos = pos

        # Build sections
        sections: list[Section] = []
        for i, (pos, level, title) in enumerate(deduped):
            # Section text is from this heading to the next
            if i + 1 < len(deduped):
                section_text = text[pos: deduped[i + 1][0]]
            else:
                section_text = text[pos:]

            sections.append(Section(
                title=title,
                level=level,
                text=section_text.strip(),
                start_index=pos,
            ))

        # If no headings found, treat whole text as one section
        if not sections:
            sections.append(Section(
                title="Main Content",
                level=1,
                text=text.strip(),
                start_index=0,
            ))

        return sections
