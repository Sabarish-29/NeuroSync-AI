"""
NeuroSync AI — Configuration settings and thresholds.

All thresholds are configurable for experiment A/B testing
and for tuning based on real student data.
"""

from __future__ import annotations

import os
from pathlib import Path


# =============================================================================
# Paths
# =============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "neurosync.db")))
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE = os.getenv("LOG_FILE", str(PROJECT_ROOT / "logs" / "neurosync.log"))

# =============================================================================
# Behavioral Thresholds
# =============================================================================
BEHAVIORAL_THRESHOLDS: dict[str, float | int] = {
    # M14 — Pseudo-understanding
    "FAST_ANSWER_THRESHOLD_MS": 3000,       # <3s = suspiciously fast
    "SLOW_ANSWER_THRESHOLD_MS": 15000,      # >15s = thoughtful

    # M07 — Frustration
    "FRUSTRATION_WATCH_THRESHOLD": 0.25,
    "FRUSTRATION_WARNING_THRESHOLD": 0.45,
    "FRUSTRATION_CRITICAL_THRESHOLD": 0.70,
    "FRUSTRATION_COOLDOWN_SECONDS": 300,    # 5 minutes

    # M10 — Fatigue
    "FATIGUE_VARIANCE_THRESHOLD": 0.65,     # CoV threshold
    "FATIGUE_SOFT_THRESHOLD": 0.50,
    "FATIGUE_MANDATORY_THRESHOLD": 0.75,
    "FATIGUE_SESSION_RISK_START_MINUTES": 15,
    "FATIGUE_SESSION_RISK_FULL_MINUTES": 35,
    "FATIGUE_BREAK_COOLDOWN_MINUTES": 20,

    # M08 — Insight
    "INSIGHT_PRECEDING_FRUSTRATION_THRESHOLD": 0.40,
    "INSIGHT_PRECEDING_DURATION_SECONDS": 60,
    "INSIGHT_RESOLUTION_SPEED_MS": 5000,
    "INSIGHT_WINDOW_DURATION_SECONDS": 180,
    "INSIGHT_COOLDOWN_MINUTES": 10,

    # M20 — Rewards
    "REWARD_MIN_INTERVAL_ANSWERS": 8,
    "REWARD_MAX_INTERVAL_ANSWERS": 12,
    "REWARD_MOTIVATION_DIP_THRESHOLD": 0.80,   # interaction speed ratio
    "REWARD_COOLDOWN_MINUTES": 5,
    "REWARD_MAX_GAP_MINUTES": 15,

    # Signal windows
    "RESPONSE_TIME_WINDOW": 10,             # last N questions
    "REWIND_WINDOW_MINUTES": 5,
    "IDLE_WINDOW_MINUTES": 5,
    "INTERACTION_VARIANCE_WINDOW": 20,      # last N events
    "SCROLL_WINDOW": 30,
    "REWIND_BURST_THRESHOLD": 3,            # rewinds in 60s = burst
    "REWIND_BURST_WINDOW_SECONDS": 60,

    # Fusion thresholds
    "HIGH_CONFIDENCE_SIGNALS_REQUIRED": 3,
    "MEDIUM_CONFIDENCE_SIGNALS_REQUIRED": 2,
    "FUSION_CYCLE_INTERVAL_MS": 500,        # run fusion every 500ms
}


def get_threshold(key: str) -> float:
    """Get a threshold value by key, raising KeyError if not found."""
    value = BEHAVIORAL_THRESHOLDS[key]
    return float(value)
