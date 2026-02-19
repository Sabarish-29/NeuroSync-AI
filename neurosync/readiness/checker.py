"""
Readiness checker — orchestrates the full pre-lesson readiness protocol.

1. Run self-report assessment
2. Run physiological (blink-rate) assessment
3. Run behavioural warmup assessment
4. Compute combined readiness score
5. If anxiety high → offer breathing exercise → optional recheck
6. Persist result to ``readiness_checks`` table
"""

from __future__ import annotations

import time
import uuid
from typing import Literal

from pydantic import BaseModel, Field

from neurosync.config.settings import READINESS_CONFIG
from neurosync.database.manager import DatabaseManager
from neurosync.readiness.assessments.behavioral import (
    BehavioralResult,
    WarmupAnswer,
    assess_warmup,
)
from neurosync.readiness.assessments.physiological import (
    PhysiologicalResult,
    assess_blink_rate,
)
from neurosync.readiness.assessments.self_report import (
    SelfReportResult,
    score_responses,
)
from neurosync.readiness.interventions.breathing import (
    total_duration_seconds,
)
from neurosync.readiness import scorer as readiness_scorer


_READY_THRESH: float = float(READINESS_CONFIG["READY_THRESHOLD"])


class ReadinessCheckResult(BaseModel):
    """Full result of a pre-lesson readiness check."""

    check_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    session_id: str
    student_id: str
    lesson_topic: str
    timestamp: float = Field(default_factory=time.time)

    self_report: SelfReportResult = Field(default_factory=SelfReportResult)
    physiological: PhysiologicalResult = Field(default_factory=PhysiologicalResult)
    behavioral: BehavioralResult = Field(default_factory=BehavioralResult)

    readiness_score: float = 1.0
    anxiety_score: float = 0.0
    status: Literal["ready", "not_ready", "needs_intervention"] = "ready"
    recommendation: str = ""

    breathing_offered: bool = False
    breathing_completed: bool = False
    manual_override: bool = False
    lesson_started: bool = False
    elapsed_time_seconds: float = 0.0


def run_check(
    *,
    session_id: str,
    student_id: str,
    lesson_topic: str,
    self_report_responses: dict[str, int] | None = None,
    blink_rate: float | None = None,
    warmup_answers: list[WarmupAnswer] | None = None,
    db: DatabaseManager | None = None,
) -> ReadinessCheckResult:
    """Execute a full readiness check and persist the result.

    All three assessment inputs are optional; missing inputs use
    fallback / neutral scores.
    """
    start = time.time()

    # 1. Self-report
    sr = score_responses(self_report_responses or {})

    # 2. Physiological
    phys = assess_blink_rate(blink_rate)

    # 3. Behavioural warmup
    behav = assess_warmup(warmup_answers or [])

    # 4. Combined score
    combined = readiness_scorer.compute(
        self_report_anxiety=sr.anxiety_score,
        physiological_anxiety=phys.anxiety_score,
        behavioral_anxiety=behav.anxiety_score,
        webcam_available=phys.available,
    )

    elapsed = round(time.time() - start, 4)

    result = ReadinessCheckResult(
        session_id=session_id,
        student_id=student_id,
        lesson_topic=lesson_topic,
        self_report=sr,
        physiological=phys,
        behavioral=behav,
        readiness_score=combined.readiness,
        anxiety_score=combined.combined_anxiety,
        status=combined.status,
        recommendation=combined.recommendation,
        breathing_offered=combined.status == "needs_intervention",
        elapsed_time_seconds=elapsed,
    )

    # 5. Persist
    if db is not None:
        _persist(db, result)

    return result


def recheck_after_intervention(
    previous: ReadinessCheckResult,
    *,
    self_report_responses: dict[str, int] | None = None,
    blink_rate: float | None = None,
    warmup_answers: list[WarmupAnswer] | None = None,
    breathing_completed: bool = False,
    db: DatabaseManager | None = None,
) -> ReadinessCheckResult:
    """Re-run the readiness check after an intervention (e.g. breathing).

    Reuses session metadata from *previous*.
    """
    updated = run_check(
        session_id=previous.session_id,
        student_id=previous.student_id,
        lesson_topic=previous.lesson_topic,
        self_report_responses=self_report_responses,
        blink_rate=blink_rate,
        warmup_answers=warmup_answers,
        db=db,
    )
    updated.breathing_offered = previous.breathing_offered
    updated.breathing_completed = breathing_completed
    return updated


# ── Persistence helper ────────────────────────────────────────────────


def _persist(db: DatabaseManager, result: ReadinessCheckResult) -> None:
    """Insert a readiness check row into the database."""
    db.execute(
        """
        INSERT INTO readiness_checks (
            check_id, session_id, student_id, lesson_topic, timestamp,
            readiness_score, anxiety_score, status,
            self_report_anxiety, physiological_anxiety, behavioral_anxiety,
            breathing_offered, breathing_completed, manual_override,
            lesson_started, elapsed_time_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.check_id,
            result.session_id,
            result.student_id,
            result.lesson_topic,
            result.timestamp,
            result.readiness_score,
            result.anxiety_score,
            result.status,
            result.self_report.anxiety_score,
            result.physiological.anxiety_score,
            result.behavioral.anxiety_score,
            int(result.breathing_offered),
            int(result.breathing_completed),
            int(result.manual_override),
            int(result.lesson_started),
            result.elapsed_time_seconds,
        ),
    )
