"""
NeuroSync AI — Spaced-repetition test fixtures (Step 8).

Provides a fresh ``DatabaseManager`` with Step 8 schema,
pre-built retention data, and scheduler instances.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from neurosync.database.manager import DatabaseManager
from neurosync.spaced_repetition.forgetting_curve.fitter import ForgettingCurveFitter
from neurosync.spaced_repetition.forgetting_curve.models import (
    FittedCurve,
    RetentionPoint,
)
from neurosync.spaced_repetition.forgetting_curve.predictor import RetentionPredictor
from neurosync.spaced_repetition.quiz.generator import ReviewQuizGenerator
from neurosync.spaced_repetition.scheduler import SpacedRepetitionScheduler


@pytest.fixture
def sr_db(tmp_path: Path) -> DatabaseManager:
    """Temporary database with full schema (incl. Step 8 tables)."""
    db = DatabaseManager(tmp_path / "sr_test.db")
    db.initialise()
    yield db  # type: ignore[misc]
    db.close()


@pytest.fixture
def fitter() -> ForgettingCurveFitter:
    return ForgettingCurveFitter()


@pytest.fixture
def predictor() -> RetentionPredictor:
    return RetentionPredictor()


@pytest.fixture
def quiz_gen() -> ReviewQuizGenerator:
    return ReviewQuizGenerator()


@pytest.fixture
def scheduler(sr_db: DatabaseManager) -> SpacedRepetitionScheduler:
    return SpacedRepetitionScheduler(db=sr_db)


@pytest.fixture
def sample_retention_4pts() -> list[RetentionPoint]:
    """4-point retention history mimicking real student data."""
    base = time.time()
    return [
        RetentionPoint(time_hours=0, score=95, timestamp=base),
        RetentionPoint(time_hours=2, score=93, timestamp=base + 7200),
        RetentionPoint(time_hours=24, score=85, timestamp=base + 86400),
        RetentionPoint(time_hours=72, score=74, timestamp=base + 259200),
    ]


@pytest.fixture
def sample_retention_2pts() -> list[RetentionPoint]:
    """Only 2 points — insufficient for fitting."""
    base = time.time()
    return [
        RetentionPoint(time_hours=0, score=95, timestamp=base),
        RetentionPoint(time_hours=2, score=90, timestamp=base + 7200),
    ]


@pytest.fixture
def fitted_curve() -> FittedCurve:
    """Pre-fitted curve with realistic parameters."""
    return FittedCurve(
        tau_days=5.0,
        r0=0.95,
        model="exponential",
        confidence=0.92,
        data_points=4,
        fitted_params={"r0": 0.95, "tau": 5.0},
    )
