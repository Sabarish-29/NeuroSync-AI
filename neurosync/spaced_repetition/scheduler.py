"""
NeuroSync AI — Main spaced-repetition scheduler.

Coordinates mastery recording, forgetting-curve fitting, review
scheduling, and quiz generation.

All database access goes through the synchronous ``DatabaseManager``
(SQLite).
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field

from neurosync.config.settings import SPACED_REPETITION_CONFIG as CFG
from neurosync.database.manager import DatabaseManager
from neurosync.spaced_repetition.forgetting_curve.fitter import ForgettingCurveFitter
from neurosync.spaced_repetition.forgetting_curve.models import (
    FittedCurve,
    RetentionPoint,
    ReviewSchedule,
)
from neurosync.spaced_repetition.forgetting_curve.predictor import RetentionPredictor
from neurosync.spaced_repetition.quiz.generator import ReviewQuizGenerator


# ── Pydantic result models ──────────────────────────────────────────


class DueReview(BaseModel):
    """A review that is due (or overdue)."""

    concept_id: str
    scheduled_at: float
    review_number: int = 1
    predicted_retention: float = 0.0
    quiz: Any = None  # ReviewQuiz when populated


class DailyReviewSchedule(BaseModel):
    """All reviews for a single day."""

    date: str = ""
    total_reviews: int = 0
    reviews: list[DueReview] = Field(default_factory=list)
    estimated_duration_minutes: int = 0


# ── Scheduler ───────────────────────────────────────────────────────


class SpacedRepetitionScheduler:
    """
    Central coordinator for the spaced-repetition engine.

    * ``record_mastery()`` — register initial mastery and schedule 1st review
    * ``record_review()``  — record a review score, refit curve, schedule next
    * ``get_due_reviews()`` — list everything due now or overdue
    """

    def __init__(
        self,
        db: DatabaseManager,
        quiz_gen: ReviewQuizGenerator | None = None,
    ) -> None:
        self._db = db
        self._fitter = ForgettingCurveFitter()
        self._predictor = RetentionPredictor()
        self._quiz_gen = quiz_gen or ReviewQuizGenerator()

    # ── public API ────────────────────────────────────────────────

    def record_mastery(
        self,
        student_id: str,
        concept_id: str,
        initial_score: float,
        timestamp: float | None = None,
    ) -> None:
        """Record that the student mastered *concept_id* and schedule the first review."""
        ts = timestamp or time.time()

        # Upsert mastery record
        retention_history = json.dumps([
            {"time_hours": 0, "score": initial_score, "timestamp": ts},
        ])
        self._db.execute(
            "INSERT OR REPLACE INTO mastery_records "
            "(record_id, student_id, concept_id, first_mastered_at, "
            " last_tested_at, authenticity_score, retention_history, "
            " review_count, next_review_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)",
            (
                f"{student_id}_{concept_id}",
                student_id,
                concept_id,
                ts,
                ts,
                initial_score / 100.0,
                retention_history,
                ts + float(CFG["FIRST_REVIEW_HOURS"]) * 3600,
            ),
        )

        # Schedule first review
        first_review_at = ts + float(CFG["FIRST_REVIEW_HOURS"]) * 3600
        self._schedule_review(student_id, concept_id, first_review_at, review_number=1, interval_type="initial")

        logger.info(
            "Mastery recorded {}/{} score={:.0f}. 1st review at {}",
            student_id, concept_id, initial_score,
            datetime.fromtimestamp(first_review_at).strftime("%Y-%m-%d %H:%M"),
        )

    # ----------------------------------------------------------------

    def record_review(
        self,
        student_id: str,
        concept_id: str,
        score: float,
        timestamp: float | None = None,
    ) -> FittedCurve:
        """
        Record a review result, refit the forgetting curve, and
        schedule the next review.

        Returns the newly fitted ``FittedCurve``.
        """
        ts = timestamp or time.time()

        # Get existing retention history
        retention_data = self._get_retention_history(student_id, concept_id)
        mastery_ts = self._get_mastery_timestamp(student_id, concept_id)
        hours_since = (ts - mastery_ts) / 3600.0

        retention_data.append(RetentionPoint(time_hours=hours_since, score=score, timestamp=ts))

        # Fit curve
        curve = self._fitter.fit_curve(retention_data)

        # Store curve
        self._store_forgetting_curve(student_id, concept_id, curve)

        # Predict next review
        schedule = self._predictor.find_review_time(curve, mastery_ts)
        schedule.concept_id = concept_id

        review_number = len(retention_data) + 1
        self._schedule_review(student_id, concept_id, schedule.review_at_timestamp, review_number, "predicted")

        # Update retention history in mastery record
        history_json = json.dumps([
            {"time_hours": p.time_hours, "score": p.score, "timestamp": p.timestamp}
            for p in retention_data
        ])
        self._db.execute(
            "UPDATE mastery_records SET retention_history = ?, last_tested_at = ?, "
            "review_count = review_count + 1, next_review_at = ? "
            "WHERE student_id = ? AND concept_id = ?",
            (history_json, ts, schedule.review_at_timestamp, student_id, concept_id),
        )

        logger.info(
            "Review {}/{} score={:.0f} τ={:.1f}d R²={:.2f} next in {:.1f}d",
            student_id, concept_id, score,
            curve.tau_days, curve.confidence, schedule.days_from_mastery,
        )
        return curve

    # ----------------------------------------------------------------

    def get_due_reviews(
        self,
        student_id: str,
        current_time: float | None = None,
    ) -> list[DueReview]:
        """Return all reviews that are due or overdue."""
        now = current_time or time.time()

        rows = self._db.fetch_all(
            "SELECT concept_id, review_at, review_number, predicted_retention "
            "FROM scheduled_reviews "
            "WHERE student_id = ? AND review_at <= ? AND completed = 0 "
            "ORDER BY review_at ASC",
            (student_id, now),
        )

        due: list[DueReview] = []
        for row in rows:
            quiz = self._quiz_gen.generate_review_quiz(
                concept_id=row["concept_id"],
                review_number=row["review_number"],
            )
            due.append(DueReview(
                concept_id=row["concept_id"],
                scheduled_at=row["review_at"],
                review_number=row["review_number"],
                predicted_retention=row["predicted_retention"] or 0.0,
                quiz=quiz,
            ))
        return due

    # ── internal helpers ──────────────────────────────────────────

    def _schedule_review(
        self,
        student_id: str,
        concept_id: str,
        review_at: float,
        review_number: int,
        interval_type: str,
    ) -> None:
        review_id = f"{student_id}_{concept_id}_{review_number}"
        self._db.execute(
            "INSERT OR REPLACE INTO scheduled_reviews "
            "(review_id, student_id, concept_id, review_at, "
            " review_number, interval_type, completed, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (review_id, student_id, concept_id, review_at, review_number, interval_type, time.time()),
        )

    def _get_retention_history(
        self,
        student_id: str,
        concept_id: str,
    ) -> list[RetentionPoint]:
        row = self._db.fetch_one(
            "SELECT retention_history FROM mastery_records "
            "WHERE student_id = ? AND concept_id = ?",
            (student_id, concept_id),
        )
        if not row or not row["retention_history"]:
            return []
        data = json.loads(row["retention_history"])
        return [RetentionPoint(**p) for p in data]

    def _get_mastery_timestamp(
        self,
        student_id: str,
        concept_id: str,
    ) -> float:
        row = self._db.fetch_one(
            "SELECT first_mastered_at FROM mastery_records "
            "WHERE student_id = ? AND concept_id = ?",
            (student_id, concept_id),
        )
        return float(row["first_mastered_at"]) if row else time.time()

    def _store_forgetting_curve(
        self,
        student_id: str,
        concept_id: str,
        curve: FittedCurve,
    ) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO forgetting_curves "
            "(curve_id, student_id, concept_id, tau_days, r0, "
            " confidence, data_points, fitted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"{student_id}_{concept_id}",
                student_id,
                concept_id,
                curve.tau_days,
                curve.r0,
                curve.confidence,
                curve.data_points,
                time.time(),
            ),
        )
