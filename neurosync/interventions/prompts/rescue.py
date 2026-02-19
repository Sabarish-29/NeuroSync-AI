"""
NeuroSync AI — M07 Frustration Rescue prompts.

Generates an empathetic rescue message with an alternative approach.
"""

from __future__ import annotations


class RescuePrompts:
    """Prompt builder for frustration rescue (M07)."""

    @staticmethod
    def build(context: dict) -> str:
        """
        Build a frustration-rescue prompt.

        Expected context keys:
            concept_name, frustration_score, failed_attempts,
            lesson_topic, grade_level.
        """
        concept = context.get("concept_name", "this concept")
        frust = context.get("frustration_score", 0.5)
        attempts = context.get("failed_attempts", 1)
        topic = context.get("lesson_topic", "the current topic")
        grade = context.get("grade_level", 8)

        level = "highly" if frust > 0.75 else "moderately"

        return (
            f'A student is {level} frustrated learning about "{concept}" '
            f"in {topic}.\n\n"
            f"They've tried {attempts} times and are about to give up.\n\n"
            "Write a rescue message that:\n"
            "1. Validates that this IS hard (don't minimize)\n"
            "2. Reframes difficulty as growth\n"
            "3. Offers a specific different approach to try\n\n"
            "Requirements:\n"
            "- 60-100 words\n"
            "- Empathetic and genuine (not fake-cheerful)\n"
            "- Propose ONE clear next step\n"
            '- Use "Let me try..." or "What if we..." framing\n'
            f"- Grade {grade} tone\n\n"
            "Return ONLY the rescue message, nothing else."
        )
