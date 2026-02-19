"""
Difficulty-adjuster intervention.

When anxiety is high, recommend starting the lesson at a lower
difficulty tier and gradually ramping up.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DifficultyAdjustment(BaseModel):
    """Recommendation to adjust initial lesson difficulty."""

    original_difficulty: str = "standard"
    recommended_difficulty: str = "easy"
    reduction_level: int = Field(
        1, ge=0, le=3,
        description="How many tiers to reduce (0 = no change, 3 = maximum)",
    )
    reason: str = ""


def recommend_adjustment(
    anxiety_score: float,
    current_difficulty: str = "standard",
) -> DifficultyAdjustment:
    """Return a difficulty adjustment based on anxiety score.

    Heuristic:
    - anxiety < 0.40  → no change (level 0)
    - 0.40 - 0.60     → drop 1 tier
    - 0.60 - 0.80     → drop 2 tiers
    - ≥ 0.80          → drop 3 tiers (maximum)
    """
    if anxiety_score < 0.40:
        level = 0
    elif anxiety_score < 0.60:
        level = 1
    elif anxiety_score < 0.80:
        level = 2
    else:
        level = 3

    tier_map = {0: current_difficulty, 1: "easy", 2: "very_easy", 3: "minimal"}
    rec = tier_map.get(level, "easy")

    return DifficultyAdjustment(
        original_difficulty=current_difficulty,
        recommended_difficulty=rec,
        reduction_level=level,
        reason=f"Anxiety {anxiety_score:.2f} → difficulty reduced by {level} tier(s)."
        if level > 0
        else "Anxiety within normal range; no adjustment needed.",
    )
