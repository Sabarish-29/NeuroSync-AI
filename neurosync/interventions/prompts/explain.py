"""
NeuroSync AI — M03 Gap Explanation prompts.

Generates a 15-second contextual explanation for an unknown concept.
"""

from __future__ import annotations

from loguru import logger


class ExplainPrompts:
    """Prompt builder for knowledge-gap explanation (M03)."""

    @staticmethod
    def build(context: dict) -> str:
        """
        Build an explanation prompt.

        Expected context keys:
            concept_name, lesson_topic, grade_level,
            missing_prerequisites (optional list[str]).
        """
        concept = context.get("concept_name", "this concept")
        topic = context.get("lesson_topic", "the current topic")
        grade = context.get("grade_level", 8)
        prereqs = context.get("missing_prerequisites", [])

        prereq_note = ""
        if prereqs:
            prereq_note = (
                f"\n\nNote: The student also doesn't know: "
                f"{', '.join(prereqs)}. Keep that in mind."
            )

        return (
            f'Explain "{concept}" to a grade {grade} student who has never '
            f"heard of it before.\n\n"
            f"Context: They're learning about {topic}.{prereq_note}\n\n"
            "Requirements:\n"
            "- 40-60 words (readable in ~15 seconds)\n"
            "- Assume zero prior knowledge\n"
            "- Use a concrete example\n"
            "- Make it memorable\n"
            "- Don't use jargon without explaining it\n\n"
            "Return ONLY the explanation, nothing else."
        )

    @staticmethod
    def validate_length(response: str) -> str:
        """Ensure explanation is 40-60 words; truncate if needed."""
        words = response.split()
        word_count = len(words)

        if 40 <= word_count <= 60:
            return response
        elif word_count < 40:
            logger.warning("Explanation too short: {} words", word_count)
            return response
        else:
            return ExplainPrompts._truncate_at_sentence(words, target=60)

    @staticmethod
    def _truncate_at_sentence(words: list[str], target: int) -> str:
        """Truncate at nearest sentence boundary before *target*."""
        for i in range(target, max(0, target - 20), -1):
            if i < len(words) and words[i - 1].endswith((".", "!", "?")):
                return " ".join(words[:i])
        return " ".join(words[:target]) + "..."
