"""Tests for the self-report anxiety assessment (Step 9)."""

from neurosync.readiness.assessments.self_report import (
    build_questions,
    score_responses,
)


class TestSelfReport:
    """Self-report assessment tests."""

    def test_build_questions_contains_topic(self) -> None:
        """Questions should embed the lesson topic string."""
        qs = build_questions("Quadratic Equations")
        assert len(qs) == 3
        assert any("Quadratic Equations" in q.text for q in qs)

    def test_high_anxiety_responses(self, high_anxiety_responses: dict[str, int]) -> None:
        """Worst-case Likert responses → anxiety close to 1.0."""
        result = score_responses(high_anxiety_responses)
        assert result.anxiety_score >= 0.9

    def test_low_anxiety_responses(self, low_anxiety_responses: dict[str, int]) -> None:
        """Best-case Likert responses → anxiety close to 0.0."""
        result = score_responses(low_anxiety_responses)
        assert result.anxiety_score <= 0.1
