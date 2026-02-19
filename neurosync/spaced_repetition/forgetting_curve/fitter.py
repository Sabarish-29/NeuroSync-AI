"""
NeuroSync AI — Forgetting-curve fitter.

Fits R(t) = R₀ · exp(−t/τ) to measured retention data using scipy.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from loguru import logger

from neurosync.config.settings import SPACED_REPETITION_CONFIG as CFG
from neurosync.spaced_repetition.forgetting_curve.models import (
    FittedCurve,
    RetentionPoint,
)


def _exponential_decay(t: np.ndarray, r0: float, tau: float) -> np.ndarray:  # type: ignore[type-arg]
    """R(t) = r0 · exp(−t / tau)"""
    return r0 * np.exp(-t / tau)


class ForgettingCurveFitter:
    """Fits an exponential forgetting curve to student retention data."""

    def __init__(
        self,
        min_data_points: int | None = None,
        default_tau: float | None = None,
    ) -> None:
        self.min_data_points: int = int(
            min_data_points or CFG["MIN_DATA_POINTS_FOR_FIT"]
        )
        self.default_tau: float = float(default_tau or CFG["DEFAULT_TAU_DAYS"])

    # ------------------------------------------------------------------
    def fit_curve(self, retention_data: list[RetentionPoint]) -> FittedCurve:
        """
        Fit forgetting curve to *retention_data*.

        If fewer than *min_data_points* are available a default curve is
        returned (τ = ``default_tau``).
        """
        if len(retention_data) < self.min_data_points:
            return FittedCurve(
                tau_days=self.default_tau,
                r0=0.95,
                model="default",
                confidence=0.0,
                data_points=len(retention_data),
            )

        times_hours = np.array([p.time_hours for p in retention_data])
        scores = np.array([p.score for p in retention_data])

        # Normalise scores → retention in 0-1
        max_score = float(np.max(scores)) or 1.0
        retention = scores / max_score

        # Convert hours → days
        times_days = times_hours / 24.0

        try:
            # Lazy-import scipy to tolerate environments where the C
            # extensions fail at import time (numpy/scipy version skew).
            from scipy.optimize import curve_fit  # noqa: WPS433

            params, _ = curve_fit(
                _exponential_decay,
                times_days,
                retention,
                p0=[0.95, self.default_tau],
                bounds=(
                    [0.5, float(CFG["TAU_LOWER_BOUND"])],
                    [1.0, float(CFG["TAU_UPPER_BOUND"])],
                ),
                maxfev=int(CFG["CURVE_FIT_MAX_ITERATIONS"]),
            )
            r0_fitted, tau_fitted = params

            # R² goodness-of-fit
            predictions = _exponential_decay(times_days, r0_fitted, tau_fitted)
            ss_res = float(np.sum((retention - predictions) ** 2))
            ss_tot = float(np.sum((retention - np.mean(retention)) ** 2))
            r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

            return FittedCurve(
                tau_days=float(tau_fitted),
                r0=float(r0_fitted),
                model="exponential",
                confidence=float(r_squared),
                data_points=len(retention_data),
                fitted_params={"r0": float(r0_fitted), "tau": float(tau_fitted)},
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning("Curve fitting failed: {}, using fallback", exc)
            return self._fallback_fit(retention_data, times_days, retention)

    # ------------------------------------------------------------------
    def _fallback_fit(
        self,
        retention_data: list[RetentionPoint],
        times_days: np.ndarray,
        retention: np.ndarray,
    ) -> FittedCurve:
        """
        Pure-Python fallback when scipy is unavailable or curve_fit fails.

        Uses log-linear regression:
            ln(R) = ln(R0) - t/τ  →  slope = -1/τ
        """
        try:
            log_ret = np.log(np.clip(retention, 1e-9, None))
            n = len(times_days)
            sum_t = float(np.sum(times_days))
            sum_lr = float(np.sum(log_ret))
            sum_t_lr = float(np.sum(times_days * log_ret))
            sum_t2 = float(np.sum(times_days ** 2))

            denom = n * sum_t2 - sum_t ** 2
            if abs(denom) < 1e-12:
                raise ValueError("degenerate data")

            slope = (n * sum_t_lr - sum_t * sum_lr) / denom
            intercept = (sum_lr - slope * sum_t) / n

            r0_fitted = float(math.exp(intercept))
            tau_fitted = -1.0 / slope if slope < 0 else self.default_tau
            tau_fitted = max(float(CFG["TAU_LOWER_BOUND"]), min(float(CFG["TAU_UPPER_BOUND"]), tau_fitted))
            r0_fitted = max(0.5, min(1.0, r0_fitted))

            # R²
            predictions = r0_fitted * np.exp(-times_days / tau_fitted)
            ss_res = float(np.sum((retention - predictions) ** 2))
            ss_tot = float(np.sum((retention - np.mean(retention)) ** 2))
            r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

            return FittedCurve(
                tau_days=tau_fitted,
                r0=r0_fitted,
                model="exponential",
                confidence=float(max(0.0, r_squared)),
                data_points=len(retention_data),
                fitted_params={"r0": r0_fitted, "tau": tau_fitted},
            )
        except Exception:  # noqa: BLE001
            return FittedCurve(
                tau_days=self.default_tau,
                r0=0.95,
                model="default",
                confidence=0.0,
                data_points=len(retention_data),
            )
