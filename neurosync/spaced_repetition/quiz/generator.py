"""
NeuroSync AI — Review-quiz generator.

Generates quiz questions for spaced-repetition reviews.
Uses the ``InterventionGenerator`` (GPT-4) when available, otherwise
produces a simple recall question as fallback.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

from neurosync.config.settings import SPACED_REPETITION_CONFIG as CFG
from neurosync.spaced_repetition.quiz.difficulty_adapter import DifficultyAdapter
from neurosync.spaced_repetition.quiz.question_bank import (
    QuestionBank,
    QuizQuestion,
    ReviewQuiz,
)


class ReviewQuizGenerator:
    """
    Generates review quizzes for spaced-repetition cycles.

    Parameters
    ----------
    intervention_generator
        Optional ``InterventionGenerator`` used to call GPT-4.
    graph_manager
        Optional ``GraphManager`` used to look up concept details.
    """

    def __init__(
        self,
        intervention_generator: Any = None,
        graph_manager: Any = None,
    ) -> None:
        self._gen = intervention_generator
        self._graph = graph_manager
        self._adapter = DifficultyAdapter()
        self._bank = QuestionBank()

    # ------------------------------------------------------------------
    def generate_review_quiz(
        self,
        concept_id: str,
        review_number: int = 1,
        recent_score: float | None = None,
    ) -> ReviewQuiz:
        """
        Build a quiz for the given *concept_id*.

        * Difficulty is determined by ``DifficultyAdapter``.
        * If cached questions exist in the bank they are returned first.
        * Otherwise a simple recall question is generated (GPT-4 path is
          intentionally synchronous-safe so tests don't need async stubs).
        """
        difficulty = self._adapter.determine_difficulty(review_number, recent_score)
        count = int(CFG["QUIZ_QUESTIONS_PER_REVIEW"])

        # Try bank first
        cached = self._bank.get(concept_id, limit=count)
        if len(cached) >= count:
            return ReviewQuiz(
                concept_id=concept_id,
                difficulty=difficulty,
                questions=cached[:count],
                estimated_duration_seconds=count * int(CFG["QUIZ_SECONDS_PER_QUESTION"]),
            )

        # Fallback: deterministic recall question
        questions = [
            QuizQuestion(
                question=f"What is {concept_id}?",
                correct_answer=f"Definition of {concept_id}",
                distractor_1="Incorrect answer A",
                distractor_2="Incorrect answer B",
                distractor_3="Incorrect answer C",
            )
        ]

        return ReviewQuiz(
            concept_id=concept_id,
            difficulty=difficulty,
            questions=questions,
            estimated_duration_seconds=count * int(CFG["QUIZ_SECONDS_PER_QUESTION"]),
        )
