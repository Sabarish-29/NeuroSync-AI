"""
NeuroSync AI — Progress Tracker.

Tracks content generation progress across all pipeline stages
and provides real-time status updates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class PipelineStage(str, Enum):
    """Stages of the content generation pipeline."""
    PARSING = "parsing"
    CLEANING = "cleaning"
    ANALYZING = "analyzing"
    EXTRACTING_CONCEPTS = "extracting_concepts"
    GENERATING_SLIDES = "generating_slides"
    GENERATING_SCRIPTS = "generating_scripts"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_VIDEO = "generating_video"
    GENERATING_STORY = "generating_story"
    GENERATING_QUIZ = "generating_quiz"
    EXPORTING = "exporting"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class StageProgress:
    """Progress info for a single stage."""
    stage: PipelineStage
    status: str = "pending"              # pending, running, completed, failed
    progress_pct: float = 0.0
    message: str = ""
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None

    @property
    def elapsed_seconds(self) -> float:
        if self.started_at is None:
            return 0.0
        end = self.completed_at or time.time()
        return end - self.started_at


@dataclass
class PipelineProgress:
    """Overall pipeline progress."""
    stages: dict[str, StageProgress] = field(default_factory=dict)
    current_stage: Optional[PipelineStage] = None
    overall_progress_pct: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None

    @property
    def elapsed_seconds(self) -> float:
        if self.started_at is None:
            return 0.0
        end = self.completed_at or time.time()
        return end - self.started_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_stage": self.current_stage.value if self.current_stage else None,
            "overall_progress_pct": round(self.overall_progress_pct, 1),
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "error": self.error,
            "stages": {
                k: {
                    "status": v.status,
                    "progress_pct": round(v.progress_pct, 1),
                    "message": v.message,
                    "elapsed_seconds": round(v.elapsed_seconds, 1),
                    "error": v.error,
                }
                for k, v in self.stages.items()
            },
        }


class ProgressTracker:
    """Track progress across content generation pipeline stages."""

    # Weight each stage contributes to overall progress
    STAGE_WEIGHTS: dict[PipelineStage, float] = {
        PipelineStage.PARSING: 0.05,
        PipelineStage.CLEANING: 0.05,
        PipelineStage.ANALYZING: 0.05,
        PipelineStage.EXTRACTING_CONCEPTS: 0.15,
        PipelineStage.GENERATING_SLIDES: 0.10,
        PipelineStage.GENERATING_SCRIPTS: 0.15,
        PipelineStage.GENERATING_AUDIO: 0.15,
        PipelineStage.GENERATING_VIDEO: 0.10,
        PipelineStage.GENERATING_STORY: 0.10,
        PipelineStage.GENERATING_QUIZ: 0.05,
        PipelineStage.EXPORTING: 0.05,
    }

    def __init__(self, callback: Optional[Callable[[PipelineProgress], None]] = None) -> None:
        self._progress = PipelineProgress()
        self._callback = callback

        # Initialize all stages as pending
        for stage in PipelineStage:
            if stage not in (PipelineStage.COMPLETE, PipelineStage.FAILED):
                self._progress.stages[stage.value] = StageProgress(
                    stage=stage, status="pending",
                )

    @property
    def progress(self) -> PipelineProgress:
        return self._progress

    def start_pipeline(self) -> None:
        """Mark pipeline as started."""
        self._progress.started_at = time.time()
        self._notify()

    def start_stage(self, stage: PipelineStage, message: str = "") -> None:
        """Mark a stage as running."""
        sp = self._progress.stages.get(stage.value)
        if sp:
            sp.status = "running"
            sp.message = message
            sp.started_at = time.time()
        self._progress.current_stage = stage
        self._update_overall()
        self._notify()

    def update_stage(self, stage: PipelineStage, progress_pct: float,
                     message: str = "") -> None:
        """Update stage progress percentage."""
        sp = self._progress.stages.get(stage.value)
        if sp:
            sp.progress_pct = min(progress_pct, 100.0)
            if message:
                sp.message = message
        self._update_overall()
        self._notify()

    def complete_stage(self, stage: PipelineStage, message: str = "") -> None:
        """Mark a stage as completed."""
        sp = self._progress.stages.get(stage.value)
        if sp:
            sp.status = "completed"
            sp.progress_pct = 100.0
            sp.completed_at = time.time()
            if message:
                sp.message = message
        self._update_overall()
        self._notify()

    def fail_stage(self, stage: PipelineStage, error: str) -> None:
        """Mark a stage as failed."""
        sp = self._progress.stages.get(stage.value)
        if sp:
            sp.status = "failed"
            sp.error = error
            sp.completed_at = time.time()
        self._progress.error = error
        self._notify()

    def complete_pipeline(self) -> None:
        """Mark the entire pipeline as complete."""
        self._progress.current_stage = PipelineStage.COMPLETE
        self._progress.overall_progress_pct = 100.0
        self._progress.completed_at = time.time()
        self._notify()

    def fail_pipeline(self, error: str) -> None:
        """Mark pipeline as failed."""
        self._progress.current_stage = PipelineStage.FAILED
        self._progress.error = error
        self._progress.completed_at = time.time()
        self._notify()

    def _update_overall(self) -> None:
        """Recalculate overall progress from stage weights."""
        total = 0.0
        for stage, weight in self.STAGE_WEIGHTS.items():
            sp = self._progress.stages.get(stage.value)
            if sp:
                total += weight * (sp.progress_pct / 100.0)
        self._progress.overall_progress_pct = total * 100.0

    def _notify(self) -> None:
        """Send progress update via callback."""
        if self._callback:
            try:
                self._callback(self._progress)
            except Exception:
                pass
