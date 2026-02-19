"""
NeuroSync AI — Review-quiz question bank.

Stores and retrieves quiz questions per concept so that the same
question isn't asked on consecutive reviews.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    """A single multiple-choice question."""

    question: str
    correct_answer: str
    distractor_1: str = ""
    distractor_2: str = ""
    distractor_3: str = ""


class ReviewQuiz(BaseModel):
    """Collection of questions for one review session."""

    concept_id: str
    difficulty: str = "medium"
    questions: list[QuizQuestion] = Field(default_factory=list)
    estimated_duration_seconds: int = 180


class QuestionBank:
    """In-memory question bank keyed by concept_id."""

    def __init__(self) -> None:
        self._bank: dict[str, list[QuizQuestion]] = {}

    def add(self, concept_id: str, questions: list[QuizQuestion]) -> None:
        self._bank.setdefault(concept_id, []).extend(questions)

    def get(self, concept_id: str, limit: int = 3) -> list[QuizQuestion]:
        return self._bank.get(concept_id, [])[:limit]

    def count(self, concept_id: str) -> int:
        return len(self._bank.get(concept_id, []))
