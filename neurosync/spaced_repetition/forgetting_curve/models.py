"""
NeuroSync AI — Forgetting-curve mathematical models.

Provides Pydantic v2 data-models used across the spaced repetition engine.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RetentionPoint(BaseModel):
    """Single retention measurement."""

    time_hours: float = Field(..., description="Hours since mastery")
    score: float = Field(..., description="Quiz score 0-100")
    timestamp: float = Field(..., description="Epoch seconds when measured")


class FittedCurve(BaseModel):
    """Fitted forgetting-curve parameters."""

    tau_days: float = Field(..., description="Decay time-constant (days)")
    r0: float = Field(..., description="Initial retention (0.0-1.0)")
    model: str = Field("default", description="'exponential' or 'default'")
    confidence: float = Field(0.0, description="R² goodness of fit")
    data_points: int = Field(0, description="Number of data points used")
    fitted_params: Optional[dict] = None


class ReviewSchedule(BaseModel):
    """Scheduled review for a single concept."""

    concept_id: str = ""
    review_at_timestamp: float = 0.0
    days_from_mastery: float = 0.0
    predicted_retention_at_review: float = 0.0
    curve_confidence: float = 0.0
