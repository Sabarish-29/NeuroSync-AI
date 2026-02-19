"""
Behavioural warmup anxiety assessment.

Has the student answer a few easy prerequisite questions and analyses
response time, accuracy and consistency to infer anxiety / distraction.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from neurosync.config.settings import READINESS_CONFIG

_RT_NORM: float = float(READINESS_CONFIG["RESPONSE_TIME_NORM_SECONDS"])
_RT_SLOW: float = float(READINESS_CONFIG["RESPONSE_TIME_SLOW_SECONDS"])
_CV_THRESH: float = float(READINESS_CONFIG["CV_THRESHOLD"])


class WarmupAnswer(BaseModel):
    """A single warmup question attempt."""

    question_id: str
    correct: bool
    response_time_seconds: float


class BehavioralResult(BaseModel):
    """Aggregated result from the behavioural warmup."""

    mean_response_time: float = Field(0.0, ge=0.0)
    cv_response_time: float = Field(
        0.0, ge=0.0,
        description="Coefficient of variation of response times",
    )
    accuracy: float = Field(0.0, ge=0.0, le=1.0)
    anxiety_score: float = Field(0.0, ge=0.0, le=1.0)


def _coefficient_of_variation(values: list[float]) -> float:
    """Return CV = std / mean (0 if mean is 0 or single value)."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    if mean == 0:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return (variance ** 0.5) / mean


def assess_warmup(answers: list[WarmupAnswer]) -> BehavioralResult:
    """Analyse warmup answers and return an anxiety estimate.

    Anxiety components (each in [0, 1]):
    - **speed**: mean RT mapped linearly from ``RT_NORM`` (0) → ``RT_SLOW`` (1)
    - **consistency**: CV above ``CV_THRESHOLD`` → scaled anxiety
    - **accuracy**: ``1 - accuracy``

    Weights: speed 0.50, consistency 0.25, accuracy 0.25
    """
    if not answers:
        return BehavioralResult(anxiety_score=0.5)

    times = [a.response_time_seconds for a in answers]
    correct_count = sum(1 for a in answers if a.correct)

    mean_rt = sum(times) / len(times)
    cv = _coefficient_of_variation(times)
    accuracy = correct_count / len(answers)

    # Speed component
    if mean_rt <= _RT_NORM:
        speed_anxiety = 0.0
    elif mean_rt >= _RT_SLOW:
        speed_anxiety = 1.0
    else:
        speed_anxiety = (mean_rt - _RT_NORM) / (_RT_SLOW - _RT_NORM)

    # Consistency component
    if cv <= _CV_THRESH:
        consistency_anxiety = 0.0
    else:
        consistency_anxiety = min((cv - _CV_THRESH) / _CV_THRESH, 1.0)

    # Accuracy component (lower accuracy → higher anxiety)
    accuracy_anxiety = 1.0 - accuracy

    anxiety = 0.50 * speed_anxiety + 0.25 * consistency_anxiety + 0.25 * accuracy_anxiety

    return BehavioralResult(
        mean_response_time=round(mean_rt, 4),
        cv_response_time=round(cv, 4),
        accuracy=round(accuracy, 4),
        anxiety_score=round(min(max(anxiety, 0.0), 1.0), 4),
    )
