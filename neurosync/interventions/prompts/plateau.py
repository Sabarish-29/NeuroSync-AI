"""
NeuroSync AI — M22 Method Overhaul / Plateau Escape prompts.

Re-explains a concept using a completely different modality (story, visual, etc.).
"""

from __future__ import annotations


class PlateauPrompts:
    """Prompt builder for method-overhaul re-explanation (M22)."""

    METHOD_INSTRUCTIONS: dict[str, str] = {
        "story_analogy": "Explain using a vivid story or analogy from everyday life",
        "visual_diagram": "Describe a visual representation (but in text form)",
        "real_world_example": "Use a concrete real-world application",
        "interactive_simulation": "Describe hands-on experimentation",
        "peer_explanation": "Write as if student is explaining to a friend",
    }

    @staticmethod
    def build(context: dict) -> str:
        """
        Build a plateau / method-overhaul prompt.

        Expected context keys:
            concept_name, concept_definition, failed_methods (list[str]),
            new_method, grade_level.
        """
        concept = context.get("concept_name", "this concept")
        definition = context.get("concept_definition", "")
        failed = context.get("failed_methods", [])
        method = context.get("new_method", "story_analogy")
        grade = context.get("grade_level", 8)

        instruction = PlateauPrompts.METHOD_INSTRUCTIONS.get(
            method, "Try a completely different approach"
        )
        methods_list = "\n".join(f"- {m}" for m in failed) if failed else "- (none)"

        return (
            f'A student has failed to understand "{concept}" after trying these approaches:\n'
            f"{methods_list}\n\n"
            f"Now try explaining it using this method: {instruction}\n\n"
            f'Concept definition (for reference): "{definition}"\n\n'
            "Requirements:\n"
            "- 80-120 words\n"
            "- Make it vivid and memorable\n"
            "- This is their last chance before giving up\n"
            f"- Grade {grade} appropriate\n"
            "- Don't mention that previous attempts failed\n\n"
            "Return ONLY the new explanation, nothing else."
        )
