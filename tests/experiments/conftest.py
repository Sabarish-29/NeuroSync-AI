"""
Shared fixtures for experiment tests.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from neurosync.experiments.framework import (
    ExperimentConfig,
    ExperimentFramework,
    ExperimentResult,
)


@pytest.fixture
def framework() -> ExperimentFramework:
    """Create an ExperimentFramework instance."""
    return ExperimentFramework()


@pytest.fixture
def control_config() -> ExperimentConfig:
    """Create a control experiment config."""
    return ExperimentConfig(
        experiment_id="E1",
        name="Test Control",
        hypothesis="Control hypothesis",
        condition="control",
        participant_id="P000",
        duration_minutes=5,
        sample_size=4,
    )


@pytest.fixture
def treatment_config() -> ExperimentConfig:
    """Create a treatment experiment config."""
    return ExperimentConfig(
        experiment_id="E1",
        name="Test Treatment",
        hypothesis="Treatment hypothesis",
        condition="treatment",
        participant_id="P001",
        duration_minutes=5,
        sample_size=4,
    )


@pytest.fixture
def sample_results() -> list[ExperimentResult]:
    """Create a batch of sample results for analysis."""
    results = []
    for i in range(10):
        cond = "control" if i % 2 == 0 else "treatment"
        quiz = 0.55 + (i % 5) * 0.05 if cond == "control" else 0.75 + (i % 5) * 0.03
        results.append(
            ExperimentResult(
                experiment_id="E1",
                participant_id=f"P{i:03d}",
                condition=cond,
                session_id=f"sess-{i}",
                quiz_score=quiz,
                completion_rate=0.7 + i * 0.02,
                rewind_count=10 - i,
                off_screen_time_seconds=120.0 - i * 10,
            )
        )
    return results


@pytest.fixture
def export_dir(tmp_path: Path) -> Path:
    """Temporary directory for export files."""
    d = tmp_path / "exports"
    d.mkdir()
    return d
