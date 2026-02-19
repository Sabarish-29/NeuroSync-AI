"""
NeuroSync AI — Text Cleaner.

Cleans and normalizes raw extracted text: removes artifacts,
normalizes whitespace, fixes encoding, and removes headers/footers.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass
class CleanedText:
    """Result of text cleaning."""
    original_length: int
    cleaned_length: int
    text: str
    sections: list[str]
    removed_artifacts: int


class TextCleaner:
    """Cleans raw PDF/document text for downstream processing."""

    # Common header/footer patterns
    HEADER_FOOTER_PATTERNS = [
        r"^Page\s+\d+\s*(of\s+\d+)?$",
        r"^\d+\s*$",                          # lone page numbers
        r"^©.*$",                             # copyright lines
        r"^All [Rr]ights [Rr]eserved.*$",
        r"^Confidential.*$",
    ]

    def __init__(self) -> None:
        self._hf_regexes = [re.compile(p, re.MULTILINE) for p in self.HEADER_FOOTER_PATTERNS]

    def clean(self, raw_text: str) -> CleanedText:
        """
        Clean raw text from PDF extraction.

        Steps:
          1. Normalize unicode
          2. Fix common PDF artifacts (ligatures, hyphenation)
          3. Remove headers/footers
          4. Normalize whitespace
          5. Split into sections

        Returns:
            CleanedText with cleaned text and metadata.
        """
        original_length = len(raw_text)
        removed = 0

        # 1. Unicode normalization
        text = unicodedata.normalize("NFKD", raw_text)

        # 2. Fix ligatures and common PDF artifacts
        ligatures = {
            "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
            "\ufb04": "ffl", "\u2018": "'", "\u2019": "'",
            "\u201c": '"', "\u201d": '"', "\u2013": "-",
            "\u2014": "--", "\u2026": "...", "\u00a0": " ",
        }
        for old, new in ligatures.items():
            count = text.count(old)
            if count:
                text = text.replace(old, new)
                removed += count

        # 3. Fix hyphenation at line breaks (word- \nrest → wordrest)
        text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

        # 4. Remove headers/footers
        for regex in self._hf_regexes:
            matches = regex.findall(text)
            removed += len(matches)
            text = regex.sub("", text)

        # 5. Normalize whitespace
        text = re.sub(r"[ \t]+", " ", text)         # collapse horizontal spaces
        text = re.sub(r"\n{3,}", "\n\n", text)       # max 2 newlines
        text = text.strip()

        # 6. Split into sections (by double newlines)
        sections = [s.strip() for s in text.split("\n\n") if s.strip()]

        return CleanedText(
            original_length=original_length,
            cleaned_length=len(text),
            text=text,
            sections=sections,
            removed_artifacts=removed,
        )

    def extract_title(self, text: str) -> str:
        """Try to extract the document title from the first few lines."""
        lines = text.strip().split("\n")[:5]
        for line in lines:
            line = line.strip()
            # Title is usually the first substantial non-numeric line
            if len(line) > 5 and not line[0].isdigit() and not line.startswith("©"):
                return line
        return "Untitled Document"
