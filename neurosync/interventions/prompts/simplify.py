"""
NeuroSync AI — M02 Simplification prompts.

Takes a complex phrase and produces a simplified version.
"""

from __future__ import annotations


class SimplifyPrompts:
    """Prompt builder for phrase simplification (M02)."""

    @staticmethod
    def build(context: dict) -> str:
        """
        Build a simplification prompt.

        Expected context keys:
            original_phrase, surrounding_sentence, subject, grade_level,
            complexity_score (optional).
        """
        grade = context.get("grade_level", 8)
        subject = context.get("subject", "this topic")
        phrase = context.get("original_phrase", "")
        sentence = context.get("surrounding_sentence", phrase)

        return (
            f"Simplify this phrase for a grade {grade} student learning {subject}.\n\n"
            f'Original phrase: "{phrase}"\n'
            f'Full sentence: "{sentence}"\n\n'
            "Requirements:\n"
            "- Maximum 15 words\n"
            "- Maintain the core meaning\n"
            "- Use simpler vocabulary\n"
            "- Keep it accurate\n"
            "- Don't add new concepts\n\n"
            "Return ONLY the simplified phrase, nothing else."
        )

    @staticmethod
    def parse_response(response: str) -> str:
        """Clean up GPT-4 response — strip quotes, enforce word limit."""
        cleaned = response.strip().strip('"').strip("'")
        words = cleaned.split()
        if len(words) > 15:
            cleaned = " ".join(words[:15]) + "..."
        return cleaned
