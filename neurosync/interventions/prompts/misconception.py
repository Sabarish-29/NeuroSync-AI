"""
NeuroSync AI — M15 Misconception Clearing prompts.

Generates an inoculation message that gently corrects a misconception.
"""

from __future__ import annotations


class MisconceptionPrompts:
    """Prompt builder for misconception clearing (M15)."""

    @staticmethod
    def build(context: dict) -> str:
        """
        Build a misconception-clearing prompt.

        Expected context keys:
            concept_name, wrong_answer, correct_answer, grade_level.
        """
        concept = context.get("concept_name", "this concept")
        wrong = context.get("wrong_answer", "")
        correct = context.get("correct_answer", "")
        grade = context.get("grade_level", 8)

        return (
            f'A student previously answered a question about "{concept}" incorrectly.\n\n'
            f'Their answer: "{wrong}"\n'
            f'Correct answer: "{correct}"\n\n'
            "Before we teach the correct version, write a brief inoculation message that:\n"
            "1. Acknowledges this is a common misconception\n"
            "2. Explains why people often think that\n"
            "3. Previews the correct version without full detail\n\n"
            "Requirements:\n"
            "- 50-80 words\n"
            '- Non-judgmental tone (never "you were wrong")\n'
            '- Use "a common misconception is..." framing\n'
            "- Don't make the student feel bad\n"
            f"- Grade {grade} appropriate\n\n"
            "Return ONLY the inoculation message, nothing else."
        )
