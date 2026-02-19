"""Tests for the behavioural warmup anxiety assessment (Step 9)."""

from neurosync.readiness.assessments.behavioral import (
    WarmupAnswer,
    assess_warmup,
)


class TestBehavioral:
    """Behavioural warmup assessment tests."""

    def test_slow_responses(self, slow_warmup_answers: list[WarmupAnswer]) -> None:
        """Slow, inaccurate answers → elevated anxiety."""
        result = assess_warmup(slow_warmup_answers)
        assert result.anxiety_score > 0.5

    def test_normal_responses(self, normal_warmup_answers: list[WarmupAnswer]) -> None:
        """Quick, accurate answers → low anxiety."""
        result = assess_warmup(normal_warmup_answers)
        assert result.anxiety_score < 0.2

    def test_high_variance(self) -> None:
        """Highly variable response times → consistency component raises anxiety."""
        answers = [
            WarmupAnswer(question_id="q1", correct=True, response_time_seconds=3.0),
            WarmupAnswer(question_id="q2", correct=True, response_time_seconds=14.0),
            WarmupAnswer(question_id="q3", correct=True, response_time_seconds=3.0),
        ]
        result = assess_warmup(answers)
        assert result.cv_response_time > 0.5
        # Anxiety should be non-trivial due to the variance
        assert result.anxiety_score > 0.05
