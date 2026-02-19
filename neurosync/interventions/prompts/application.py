"""
NeuroSync AI — M18 Application / Transfer Testing prompts.

Generates 3 novel real-world application questions to test transfer.
"""

from __future__ import annotations

import json
import re

from loguru import logger


class ApplicationPrompts:
    """Prompt builder for application-question generation (M18)."""

    @staticmethod
    def build(context: dict) -> str:
        """
        Build an application-question prompt.

        Expected context keys:
            concept_name, concept_definition, grade_level, subject.
        """
        concept = context.get("concept_name", "this concept")
        definition = context.get("concept_definition", "")
        grade = context.get("grade_level", 8)
        subject = context.get("subject", "this subject")

        return (
            f'A student understands the theory of "{concept}" but we need '
            "to test if they can APPLY it.\n\n"
            f'Definition: "{definition}"\n\n'
            "Generate 3 real-world questions that require applying this concept "
            "to a new situation.\n\n"
            "Requirements:\n"
            "- Each question 10-20 words\n"
            "- Cannot be answered by just recalling the definition\n"
            "- Require genuine understanding and reasoning\n"
            f"- Use realistic scenarios a grade {grade} student would recognize\n"
            "- No hypothetical sci-fi scenarios\n\n"
            'Format: Return as JSON array of strings.\n'
            'Example: ["Question 1 text", "Question 2 text", "Question 3 text"]\n\n'
            "Return ONLY the JSON array, nothing else."
        )

    @staticmethod
    def parse_response(response: str) -> list[str]:
        """Parse the JSON array of questions from GPT-4 output."""
        try:
            questions = json.loads(response)
            if isinstance(questions, list) and len(questions) == 3:
                return [str(q) for q in questions]
            raise ValueError("Expected exactly 3 questions")
        except (json.JSONDecodeError, ValueError):
            # Try line-by-line extraction
            lines = [ln.strip() for ln in response.split("\n") if ln.strip()]
            cleaned: list[str] = []
            for line in lines[:3]:
                line = re.sub(r'^[\d.\-*\[\]"\s]+', "", line)
                line = line.strip('"').strip("'").rstrip(",").rstrip("]").strip()
                if line:
                    cleaned.append(line)
            if len(cleaned) == 3:
                return cleaned
            logger.error("Failed to parse application questions from GPT-4")
            raise ValueError("Could not parse questions")
