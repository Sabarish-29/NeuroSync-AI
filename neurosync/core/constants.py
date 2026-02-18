"""
NeuroSync AI — Constants for moment IDs, event types, and enumerations.
"""

from __future__ import annotations

from typing import Final

# =============================================================================
# Moment IDs — the 22 learning failure moments
# =============================================================================
MOMENT_ATTENTION_DROP: Final[str] = "M01"
MOMENT_COGNITIVE_OVERLOAD: Final[str] = "M02"
MOMENT_KNOWLEDGE_GAP: Final[str] = "M03"
MOMENT_MASTERY_VERIFICATION: Final[str] = "M04"
MOMENT_PRE_LESSON_ANXIETY: Final[str] = "M05"
MOMENT_STEALTH_BOREDOM: Final[str] = "M06"
MOMENT_FRUSTRATION: Final[str] = "M07"
MOMENT_INSIGHT: Final[str] = "M08"
MOMENT_CONFIDENCE_COLLAPSE: Final[str] = "M09"
MOMENT_FATIGUE: Final[str] = "M10"
MOMENT_PHYSICAL_DISCOMFORT: Final[str] = "M11"
MOMENT_CIRCADIAN_PEAK: Final[str] = "M12"
MOMENT_WRONG_METHOD: Final[str] = "M13"
MOMENT_PSEUDO_UNDERSTANDING: Final[str] = "M14"
MOMENT_MISCONCEPTION: Final[str] = "M15"
MOMENT_WORKING_MEMORY_OVERFLOW: Final[str] = "M16"
MOMENT_FORGETTING_CURVE: Final[str] = "M17"
MOMENT_TRANSFER_FAILURE: Final[str] = "M18"
MOMENT_SLEEP_WINDOW: Final[str] = "M19"
MOMENT_DOPAMINE_CRASH: Final[str] = "M20"
MOMENT_INTERRUPTION: Final[str] = "M21"
MOMENT_PLATEAU_ESCAPE: Final[str] = "M22"

ALL_MOMENTS: Final[list[str]] = [
    MOMENT_ATTENTION_DROP, MOMENT_COGNITIVE_OVERLOAD, MOMENT_KNOWLEDGE_GAP,
    MOMENT_MASTERY_VERIFICATION, MOMENT_PRE_LESSON_ANXIETY, MOMENT_STEALTH_BOREDOM,
    MOMENT_FRUSTRATION, MOMENT_INSIGHT, MOMENT_CONFIDENCE_COLLAPSE,
    MOMENT_FATIGUE, MOMENT_PHYSICAL_DISCOMFORT, MOMENT_CIRCADIAN_PEAK,
    MOMENT_WRONG_METHOD, MOMENT_PSEUDO_UNDERSTANDING, MOMENT_MISCONCEPTION,
    MOMENT_WORKING_MEMORY_OVERFLOW, MOMENT_FORGETTING_CURVE, MOMENT_TRANSFER_FAILURE,
    MOMENT_SLEEP_WINDOW, MOMENT_DOPAMINE_CRASH, MOMENT_INTERRUPTION,
    MOMENT_PLATEAU_ESCAPE,
]

# =============================================================================
# Event types
# =============================================================================
EVENT_TYPES: Final[list[str]] = [
    "video_play", "video_pause", "video_seek", "video_rewind",
    "question_shown", "question_answered", "answer_submitted",
    "lesson_started", "lesson_ended", "tab_hidden", "tab_visible",
    "scroll", "mouse_idle", "mouse_active", "click",
    "page_load", "session_start", "session_end",
]

# =============================================================================
# Frustration levels
# =============================================================================
FRUSTRATION_NONE: Final[str] = "none"
FRUSTRATION_WATCH: Final[str] = "watch"
FRUSTRATION_WARNING: Final[str] = "warning"
FRUSTRATION_CRITICAL: Final[str] = "critical"

# =============================================================================
# Fatigue levels
# =============================================================================
FATIGUE_FRESH: Final[str] = "fresh"
FATIGUE_MILD: Final[str] = "mild"
FATIGUE_TIRED: Final[str] = "tired"
FATIGUE_CRITICAL: Final[str] = "critical"

# =============================================================================
# Mastery flags
# =============================================================================
MASTERY_ACCEPT: Final[str] = "accept"
MASTERY_PROBE: Final[str] = "probe"
MASTERY_FLAG: Final[str] = "flag"

# =============================================================================
# Intervention urgency
# =============================================================================
URGENCY_IMMEDIATE: Final[str] = "immediate"
URGENCY_NEXT_PAUSE: Final[str] = "next_pause"
URGENCY_DEFERRED: Final[str] = "deferred"

# =============================================================================
# Response time trends
# =============================================================================
TREND_STABLE: Final[str] = "stable"
TREND_INCREASING: Final[str] = "increasing"
TREND_DECREASING: Final[str] = "decreasing"

# =============================================================================
# Scroll patterns
# =============================================================================
SCROLL_ENGAGED: Final[str] = "engaged"
SCROLL_SKIMMING: Final[str] = "skimming"
SCROLL_RUSHING: Final[str] = "rushing"

# =============================================================================
# Reward types
# =============================================================================
REWARD_TYPES: Final[list[str]] = [
    "streak", "mastery", "speed", "consistency", "explorer",
]

# =============================================================================
# Concept categories (Step 3 — Knowledge Graph)
# =============================================================================
CONCEPT_CATEGORY_CORE: Final[str] = "core"
CONCEPT_CATEGORY_PREREQUISITE: Final[str] = "prerequisite"
CONCEPT_CATEGORY_EXTENSION: Final[str] = "extension"
CONCEPT_CATEGORY_APPLICATION: Final[str] = "application"
CONCEPT_CATEGORY_MISCONCEPTION: Final[str] = "misconception"

CONCEPT_CATEGORIES: Final[list[str]] = [
    CONCEPT_CATEGORY_CORE,
    CONCEPT_CATEGORY_PREREQUISITE,
    CONCEPT_CATEGORY_EXTENSION,
    CONCEPT_CATEGORY_APPLICATION,
    CONCEPT_CATEGORY_MISCONCEPTION,
]

# =============================================================================
# Graph mastery levels (Step 3)
# =============================================================================
GRAPH_MASTERY_NOVICE: Final[str] = "novice"
GRAPH_MASTERY_DEVELOPING: Final[str] = "developing"
GRAPH_MASTERY_PROFICIENT: Final[str] = "proficient"
GRAPH_MASTERY_MASTERED: Final[str] = "mastered"

GRAPH_MASTERY_LEVELS: Final[list[str]] = [
    GRAPH_MASTERY_NOVICE,
    GRAPH_MASTERY_DEVELOPING,
    GRAPH_MASTERY_PROFICIENT,
    GRAPH_MASTERY_MASTERED,
]

# =============================================================================
# Graph relationship types (Step 3)
# =============================================================================
REL_PREREQUISITE: Final[str] = "REQUIRES"
REL_HAS_MISCONCEPTION: Final[str] = "HAS_MISCONCEPTION"
REL_STUDIED: Final[str] = "STUDIED"
REL_MASTERED: Final[str] = "MASTERED"
REL_STRUGGLES_WITH: Final[str] = "STRUGGLES_WITH"
REL_NEXT_CONCEPT: Final[str] = "NEXT_CONCEPT"
