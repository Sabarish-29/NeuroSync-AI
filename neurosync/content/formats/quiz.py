"""
NeuroSync AI — Quiz Format Handler.

Handles quiz bank export to JSON format.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class QuizOutput:
    """Quiz bank output descriptor."""
    path: str
    title: str
    question_count: int
    total_points: int
    concept_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "application/json",
            "path": self.path,
            "title": self.title,
            "question_count": self.question_count,
            "total_points": self.total_points,
            "concept_count": self.concept_count,
        }

    def exists(self) -> bool:
        return Path(self.path).exists()


class QuizExporter:
    """Export quiz banks to JSON format."""

    def export(self, quiz_bank: Any, output_path: str | Path) -> QuizOutput:
        """
        Export a QuizBank to a JSON file.

        Args:
            quiz_bank: QuizBank object.
            output_path: Where to save the JSON file.

        Returns:
            QuizOutput descriptor.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = quiz_bank.to_dict()
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        return QuizOutput(
            path=str(path),
            title=quiz_bank.title,
            question_count=len(quiz_bank.questions),
            total_points=quiz_bank.total_points,
            concept_count=len(quiz_bank.concept_coverage),
        )
