"""
NeuroSync AI — Keyword Extractor.

Extracts significant keywords/noun phrases from student text using TextBlob.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from loguru import logger

from neurosync.config.settings import NLP_THRESHOLDS

# Common English stop words to filter out
_STOP_WORDS: set[str] = {
    "the", "a", "an", "is", "was", "are", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "don", "now", "and", "but", "or", "if", "this", "that", "these",
    "those", "i", "me", "my", "we", "our", "you", "your", "he", "him",
    "his", "she", "her", "it", "its", "they", "them", "their", "what",
    "which", "who", "whom", "about", "get", "got", "also", "like",
    "think", "know", "really", "much", "well", "even", "still",
}


@dataclass
class KeywordResult:
    """Result from keyword extraction."""
    keywords: list[str] = field(default_factory=list)
    noun_phrases: list[str] = field(default_factory=list)
    keyword_count: int = 0


class KeywordExtractor:
    """
    Extracts keywords and noun phrases from student text.

    Combines TextBlob noun phrase extraction with frequency-based keyword
    selection, filtering out stop words and short tokens.
    """

    def __init__(self) -> None:
        self._max_keywords = int(NLP_THRESHOLDS["KEYWORD_MAX_KEYWORDS"])
        self._min_word_length = int(NLP_THRESHOLDS["KEYWORD_MIN_WORD_LENGTH"])

    def extract(self, text: str) -> KeywordResult:
        """Extract keywords and noun phrases from text."""
        if not text or not text.strip():
            return KeywordResult()

        # Get noun phrases via TextBlob
        noun_phrases: list[str] = []
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            noun_phrases = [np.lower() for np in blob.noun_phrases]
        except Exception as exc:
            logger.warning("TextBlob noun phrase extraction failed: {}", exc)

        # Frequency-based keyword extraction
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        filtered = [
            w for w in words
            if w not in _STOP_WORDS and len(w) >= self._min_word_length
        ]

        # Count frequencies
        freq: dict[str, int] = {}
        for w in filtered:
            freq[w] = freq.get(w, 0) + 1

        # Sort by frequency descending, take top N
        sorted_kw = sorted(freq.keys(), key=lambda k: freq[k], reverse=True)
        keywords = sorted_kw[: self._max_keywords]

        return KeywordResult(
            keywords=keywords,
            noun_phrases=noun_phrases,
            keyword_count=len(keywords),
        )

    def compute_overlap(self, extracted: list[str], expected: list[str]) -> float:
        """
        Compute keyword overlap ratio between extracted keywords and expected concept keywords.

        Returns a float in [0, 1].
        """
        if not expected:
            return 0.0
        extracted_set = {k.lower() for k in extracted}
        expected_set = {k.lower() for k in expected}
        if not expected_set:
            return 0.0
        overlap = extracted_set & expected_set
        return len(overlap) / len(expected_set)
