"""
Prerequisite-review intervention.

When a student is not ready, suggest a short review of prerequisite
concepts before diving into the new lesson.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PrerequisiteReview(BaseModel):
    """A recommendation to review prerequisites."""

    lesson_topic: str
    prerequisite_topics: list[str] = Field(default_factory=list)
    estimated_minutes: float = Field(5.0, ge=0.0)
    reason: str = "Prerequisite review suggested to improve readiness."


def suggest_review(
    lesson_topic: str,
    prerequisite_topics: list[str] | None = None,
) -> PrerequisiteReview:
    """Build a prerequisite-review recommendation.

    Parameters
    ----------
    lesson_topic:
        The upcoming lesson topic.
    prerequisite_topics:
        Known prerequisite topics (from knowledge graph or curriculum).
        If *None*, an empty list is used and the student can choose.
    """
    topics = prerequisite_topics or []
    minutes = max(3.0, 2.0 * len(topics)) if topics else 5.0
    return PrerequisiteReview(
        lesson_topic=lesson_topic,
        prerequisite_topics=topics,
        estimated_minutes=round(minutes, 1),
    )
