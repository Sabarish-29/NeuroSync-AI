"""
Main Experiment Orchestrator.

Manages controlled experiments comparing NeuroSync (treatment) vs
baseline (control) learning sessions.  Each experiment follows a
protocol that specifies content, duration, metrics, and analysis.
"""

from __future__ import annotations

import asyncio
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

from loguru import logger


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class SessionConfig:
    """Configuration applied to one participant's learning session."""

    session_id: str
    student_id: str
    ai_enabled: bool = True
    webcam_enabled: bool = False
    eeg_enabled: bool = False
    experiment_group: str = "treatment"


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment protocol."""

    experiment_id: str                        # "E1" – "E5"
    name: str
    hypothesis: str
    condition: Literal["control", "treatment", "ablation"] = "control"
    participant_id: str = ""                  # filled at runtime
    lesson_content: str = ""                  # path / identifier
    duration_minutes: int = 15
    metrics: list[str] = field(default_factory=lambda: [
        "quiz_score", "completion_rate", "rewind_count",
        "off_screen_time", "self_report",
    ])
    sample_size: int = 30
    ablation_features: list[str] = field(default_factory=list)


@dataclass
class BehavioralMetrics:
    """Aggregate behavioural stats from a session."""

    completion_rate: float = 1.0
    duration_seconds: float = 0.0
    rewind_count: int = 0
    idle_time_seconds: float = 0.0
    off_screen_time_seconds: float = 0.0


@dataclass
class SelfReportData:
    """Post-session self-report questionnaire answers."""

    focus: Optional[int] = None         # 1-5
    difficulty: Optional[int] = None    # 1-5
    frustration: Optional[int] = None   # 1-5


@dataclass
class ExperimentResult:
    """Results from one participant's experiment run."""

    experiment_id: str
    participant_id: str
    condition: str
    session_id: str

    # Performance
    quiz_score: Optional[float] = None
    completion_rate: float = 1.0
    time_spent_seconds: float = 0.0

    # Behavioural
    rewind_count: int = 0
    idle_time_seconds: float = 0.0
    off_screen_time_seconds: float = 0.0

    # Moments
    moments_fired: dict[str, int] = field(default_factory=dict)
    interventions_received: int = 0

    # Self-report
    self_reported_focus: Optional[int] = None
    self_reported_difficulty: Optional[int] = None
    self_reported_frustration: Optional[int] = None

    # Retention (for E3)
    retention_day_7: Optional[float] = None
    retention_day_30: Optional[float] = None

    # Export
    session_data_path: str = ""


# ---------------------------------------------------------------------------
# Framework
# ---------------------------------------------------------------------------

class ExperimentFramework:
    """Orchestrates controlled experiments end-to-end."""

    EXPERIMENT_IDS = ("E1", "E2", "E3", "E4", "E5")

    def __init__(self, db_manager: Any = None):
        self.db = db_manager
        self._results: list[ExperimentResult] = []

    # -- public API ---------------------------------------------------------

    async def run_experiment(
        self,
        config: ExperimentConfig,
    ) -> ExperimentResult:
        """Run one participant through a configured experiment."""
        session_id = str(uuid.uuid4())

        session_cfg = self._build_session_config(session_id, config)

        logger.info(
            f"[{config.experiment_id}] Starting {config.condition} session "
            f"for {config.participant_id}"
        )

        # Simulate lesson execution (real impl would drive orchestrator)
        start = time.time()
        behavioral = await self._simulate_lesson(session_cfg, config)
        elapsed = time.time() - start

        # Collect quiz score
        quiz_score: Optional[float] = None
        if "quiz_score" in config.metrics:
            quiz_score = await self._administer_quiz(config)

        # Collect self-report
        self_report = await self._collect_self_report(config)

        # Compute moment counts (simulated)
        moment_counts = self._generate_moment_counts(config)

        # Build result
        result = ExperimentResult(
            experiment_id=config.experiment_id,
            participant_id=config.participant_id,
            condition=config.condition,
            session_id=session_id,
            quiz_score=quiz_score,
            completion_rate=behavioral.completion_rate,
            time_spent_seconds=behavioral.duration_seconds or elapsed,
            rewind_count=behavioral.rewind_count,
            idle_time_seconds=behavioral.idle_time_seconds,
            off_screen_time_seconds=behavioral.off_screen_time_seconds,
            moments_fired=moment_counts,
            interventions_received=sum(moment_counts.values()),
            self_reported_focus=self_report.focus,
            self_reported_difficulty=self_report.difficulty,
            self_reported_frustration=self_report.frustration,
            session_data_path="",
        )

        self._results.append(result)
        return result

    async def run_batch(
        self,
        experiment_id: str,
        num_participants: int,
    ) -> list[ExperimentResult]:
        """Run *num_participants* through experiment (half control, half treatment)."""
        if experiment_id not in self.EXPERIMENT_IDS:
            raise ValueError(f"Unknown experiment: {experiment_id}")

        results: list[ExperimentResult] = []
        for i in range(num_participants):
            condition: Literal["control", "treatment"] = (
                "control" if i % 2 == 0 else "treatment"
            )
            config = self.load_protocol(experiment_id, condition)
            config.participant_id = f"P{i:03d}"

            result = await self.run_experiment(config)
            results.append(result)

        return results

    def load_protocol(
        self,
        experiment_id: str,
        condition: str,
    ) -> ExperimentConfig:
        """Load experiment config from protocols package."""
        configs = _PROTOCOL_REGISTRY.get(experiment_id)
        if configs is None:
            raise ValueError(f"Unknown experiment: {experiment_id}")
        if condition not in configs:
            raise ValueError(
                f"Unknown condition '{condition}' for {experiment_id}"
            )
        # Return a copy so callers can mutate participant_id
        import copy
        return copy.deepcopy(configs[condition])

    @property
    def results(self) -> list[ExperimentResult]:
        return list(self._results)

    # -- internals ----------------------------------------------------------

    def _build_session_config(
        self, session_id: str, config: ExperimentConfig
    ) -> SessionConfig:
        if config.condition == "control":
            return SessionConfig(
                session_id=session_id,
                student_id=config.participant_id,
                ai_enabled=False,
                webcam_enabled=False,
                experiment_group="control",
            )
        elif config.condition == "treatment":
            return SessionConfig(
                session_id=session_id,
                student_id=config.participant_id,
                ai_enabled=True,
                webcam_enabled=True,
                experiment_group="treatment",
            )
        else:  # ablation
            return SessionConfig(
                session_id=session_id,
                student_id=config.participant_id,
                ai_enabled=True,
                webcam_enabled="webcam" not in config.ablation_features,
                experiment_group="ablation",
            )

    async def _simulate_lesson(
        self,
        session_cfg: SessionConfig,
        config: ExperimentConfig,
    ) -> BehavioralMetrics:
        """Simulate a lesson (randomised metrics influenced by condition)."""
        rng = random.Random(hash(config.participant_id))

        is_treatment = config.condition == "treatment"
        duration = config.duration_minutes * 60.0

        # Treatment group gets better metrics on average
        if is_treatment:
            completion = rng.uniform(0.85, 1.0)
            rewinds = rng.randint(0, 3)
            idle = rng.uniform(5, 30)
            off_screen = rng.uniform(10, 60)
        else:
            completion = rng.uniform(0.55, 0.95)
            rewinds = rng.randint(2, 10)
            idle = rng.uniform(20, 90)
            off_screen = rng.uniform(50, 180)

        return BehavioralMetrics(
            completion_rate=round(completion, 3),
            duration_seconds=round(duration + rng.uniform(-60, 60), 1),
            rewind_count=rewinds,
            idle_time_seconds=round(idle, 1),
            off_screen_time_seconds=round(off_screen, 1),
        )

    async def _administer_quiz(self, config: ExperimentConfig) -> float:
        """Return a simulated quiz score."""
        rng = random.Random(hash(config.participant_id) + 1)
        base = 0.55 if config.condition == "control" else 0.75
        return round(min(1.0, base + rng.uniform(0, 0.25)), 3)

    async def _collect_self_report(self, config: ExperimentConfig) -> SelfReportData:
        rng = random.Random(hash(config.participant_id) + 2)
        if config.condition == "treatment":
            return SelfReportData(
                focus=rng.randint(3, 5),
                difficulty=rng.randint(2, 4),
                frustration=rng.randint(1, 3),
            )
        return SelfReportData(
            focus=rng.randint(1, 4),
            difficulty=rng.randint(2, 5),
            frustration=rng.randint(2, 5),
        )

    def _generate_moment_counts(self, config: ExperimentConfig) -> dict[str, int]:
        from neurosync.core.constants import ALL_MOMENTS

        rng = random.Random(hash(config.participant_id) + 3)
        counts: dict[str, int] = {}
        for m in ALL_MOMENTS:
            if config.condition == "treatment":
                counts[m] = rng.randint(0, 5)
            else:
                counts[m] = 0
        return counts


# ---------------------------------------------------------------------------
# Protocol registry — lazily populated on first import
# ---------------------------------------------------------------------------

_PROTOCOL_REGISTRY: dict[str, dict[str, ExperimentConfig]] = {}


def _register_protocols() -> None:
    """Import all protocol modules to populate the registry."""
    from neurosync.experiments.protocols.e1_attention import E1_CONFIG
    from neurosync.experiments.protocols.e2_overload import E2_CONFIG
    from neurosync.experiments.protocols.e3_retention import E3_CONFIG
    from neurosync.experiments.protocols.e4_frustration import E4_CONFIG
    from neurosync.experiments.protocols.e5_transfer import E5_CONFIG

    _PROTOCOL_REGISTRY.update({
        "E1": E1_CONFIG,
        "E2": E2_CONFIG,
        "E3": E3_CONFIG,
        "E4": E4_CONFIG,
        "E5": E5_CONFIG,
    })


def _ensure_protocols() -> None:
    if not _PROTOCOL_REGISTRY:
        _register_protocols()


# Monkey-patch load_protocol to ensure lazy init
_orig_load = ExperimentFramework.load_protocol


def _patched_load(self: ExperimentFramework, eid: str, cond: str) -> ExperimentConfig:
    _ensure_protocols()
    return _orig_load(self, eid, cond)


ExperimentFramework.load_protocol = _patched_load  # type: ignore[assignment]
