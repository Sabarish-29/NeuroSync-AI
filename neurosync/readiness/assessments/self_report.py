"""
Self-report anxiety assessment.

Presents three questions about the upcoming topic and converts Likert-scale
responses (1-5) into a normalised anxiety score in [0, 1].
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SelfReportQuestion(BaseModel):
    """A single Likert-scale question."""

    question_id: str
    text: str
    min_label: str = "Not at all"
    max_label: str = "Extremely"


class SelfReportResult(BaseModel):
    """Aggregated result from the self-report questionnaire."""

    responses: dict[str, int] = Field(
        default_factory=dict,
        description="question_id → Likert response (1-5)",
    )
    anxiety_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Normalised anxiety score (0 = calm, 1 = highly anxious)",
    )


# ── Pre-built question bank ──────────────────────────────────────────


def build_questions(topic: str) -> list[SelfReportQuestion]:
    """Return the three canonical readiness questions for *topic*."""
    return [
        SelfReportQuestion(
            question_id="familiarity",
            text=f"How familiar are you with '{topic}'?",
            min_label="Not at all familiar",
            max_label="Very familiar",
        ),
        SelfReportQuestion(
            question_id="difficulty_perception",
            text=f"How difficult do you expect '{topic}' to be?",
            min_label="Very easy",
            max_label="Very difficult",
        ),
        SelfReportQuestion(
            question_id="emotional_state",
            text="How anxious or stressed are you feeling right now?",
            min_label="Completely calm",
            max_label="Extremely anxious",
        ),
    ]


def score_responses(responses: dict[str, int]) -> SelfReportResult:
    """Convert Likert responses to an anxiety score.

    Mapping per question:
    - **familiarity**: higher familiarity → lower anxiety.  anxiety = (5 - r) / 4
    - **difficulty_perception**: higher perceived difficulty → higher anxiety.  anxiety = (r - 1) / 4
    - **emotional_state**: direct mapping.  anxiety = (r - 1) / 4

    The overall score is the mean of all individual anxiety values.
    """
    if not responses:
        return SelfReportResult(responses=responses, anxiety_score=0.5)

    scores: list[float] = []
    for qid, response in responses.items():
        r = max(1, min(5, response))  # clamp to 1-5
        if qid == "familiarity":
            scores.append((5 - r) / 4.0)
        else:
            # difficulty_perception & emotional_state
            scores.append((r - 1) / 4.0)

    anxiety = sum(scores) / len(scores) if scores else 0.5
    return SelfReportResult(responses=responses, anxiety_score=round(anxiety, 4))
