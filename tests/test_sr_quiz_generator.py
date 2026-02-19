"""
Step 8 — Review quiz-generator tests (2 tests).
"""

from __future__ import annotations

import pytest

from neurosync.spaced_repetition.quiz.generator import ReviewQuizGenerator


class TestReviewQuizGenerator:

    def test_generate_review_quiz_creates_questions(self, quiz_gen: ReviewQuizGenerator):
        """A quiz should contain at least 1 question."""
        quiz = quiz_gen.generate_review_quiz("photosynthesis")
        assert len(quiz.questions) >= 1
        assert quiz.concept_id == "photosynthesis"

    def test_difficulty_affects_question_complexity(self, quiz_gen: ReviewQuizGenerator):
        """Review number drives difficulty label."""
        q1 = quiz_gen.generate_review_quiz("osmosis", review_number=1)
        q3 = quiz_gen.generate_review_quiz("osmosis", review_number=3)
        assert q1.difficulty == "easy"
        assert q3.difficulty == "hard"
