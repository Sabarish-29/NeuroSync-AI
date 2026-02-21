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


# =============================================================================
# Webcam Thresholds (Step 2)
# =============================================================================
WEBCAM_THRESHOLDS: dict[str, float | int] = {
    # Gaze (M01)
    "GAZE_OFF_SCREEN_TRIGGER_MS": 4000,
    "GAZE_SCREEN_CENTER_TOLERANCE": 0.15,
    "GAZE_CONFIDENCE_MINIMUM": 0.60,

    # Blink (M10 boost)
    "BLINK_FATIGUE_HIGH_RATE": 25,       # blinks/min
    "BLINK_FATIGUE_LOW_RATE": 8,
    "BLINK_ANXIETY_RATE": 30,
    "BLINK_FLOW_RATE": 8,
    "EAR_BLINK_THRESHOLD": 0.20,

    # Expression (M07 boost)
    "EXPRESSION_FRUSTRATION_THRESHOLD": 0.55,
    "EXPRESSION_BOREDOM_THRESHOLD": 0.60,
    "EXPRESSION_EMA_ALPHA": 0.30,        # smoothing factor

    # Pose (M11)
    "FIDGET_VARIANCE_THRESHOLD": 0.018,
    "POSTURE_WINDOW_FRAMES": 90,

    # rPPG (secondary only)
    "RPPG_BUFFER_SECONDS": 10,
    "RPPG_BANDPASS_LOW": 0.7,
    "RPPG_BANDPASS_HIGH": 3.5,
    "RPPG_QUALITY_THRESHOLD": 0.50,
    "RPPG_STRESS_HR_THRESHOLD": 90,

    # Fusion
    "WEBCAM_FUSION_INTERVAL_SECONDS": 1.0,
    "WEBCAM_FACE_REQUIRED_CONFIDENCE": 0.70,
    "WEBCAM_FRAME_ROLLING_WINDOW": 30,   # frames for majority vote
}


# =============================================================================
# Neo4j Configuration (Step 3)
# =============================================================================
NEO4J_CONFIG: dict[str, object] = {
    "URI": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "USER": os.getenv("NEO4J_USER", "neo4j"),
    "PASSWORD": os.getenv("NEO4J_PASSWORD", "neurosync"),
    "DATABASE": os.getenv("NEO4J_DATABASE", "neo4j"),
    "MAX_CONNECTION_POOL_SIZE": 50,
    "CONNECTION_TIMEOUT_SECONDS": 5,
    "RETRY_ATTEMPTS": 3,
    "RETRY_DELAY_SECONDS": 1.0,
}


# =============================================================================
# Knowledge Graph Thresholds (Step 3)
# =============================================================================
KNOWLEDGE_THRESHOLDS: dict[str, float | int] = {
    # M03 — Knowledge Gap
    "GAP_PREREQUISITE_MASTERY_MIN": 0.40,     # below this = gap
    "GAP_FAILURE_STREAK_TRIGGER": 3,          # consecutive failures
    "GAP_CONFIDENCE_BOOST_FACTOR": 0.15,      # boost when prerequisite strong

    # M06 — Stealth Boredom (mastery plateau)
    "BOREDOM_MASTERY_CEILING": 0.90,          # above this = already mastered
    "BOREDOM_REPEAT_THRESHOLD": 5,            # same concept N times
    "BOREDOM_ADVANCE_SCORE": 0.85,            # suggest harder material

    # M09 — Confidence Collapse (mirror)
    "COLLAPSE_SCORE_DROP_THRESHOLD": 0.25,    # drop ≥ 25% = collapse
    "COLLAPSE_WINDOW_SECONDS": 300,           # within 5 minutes
    "COLLAPSE_RECOVERY_TARGET": 0.60,         # recovery milestone

    # M15 — Misconception
    "MISCONCEPTION_REPEAT_WRONG_THRESHOLD": 2,  # same wrong answer N times
    "MISCONCEPTION_CONFIDENCE_MIN": 0.50,        # student thinks they're right
    "MISCONCEPTION_PENALTY_FACTOR": 0.30,        # mastery score penalty

    # M16 — Working Memory Overflow (chunk tracker)
    "CHUNK_MAX_NEW_CONCEPTS": 4,              # max new concepts at once
    "CHUNK_WINDOW_MINUTES": 10,               # within N minutes
    "CHUNK_MASTERY_NEW_THRESHOLD": 0.30,      # below = still new

    # M22 — Plateau Escape
    "PLATEAU_MIN_ATTEMPTS": 8,                # min attempts to detect
    "PLATEAU_VARIANCE_MAX": 0.05,             # score variance < 5% = plateau
    "PLATEAU_DURATION_MINUTES": 15,           # for at least N minutes
    "PLATEAU_STRATEGY_SWITCH_SCORE": 0.55,    # try alternative approach

    # General graph
    "MASTERY_DECAY_RATE_PER_DAY": 0.02,       # forgetting curve
    "MASTERY_INITIAL_SCORE": 0.0,
    "MASTERY_MAX_SCORE": 1.0,
    "MASTERY_CORRECT_INCREMENT": 0.15,
    "MASTERY_INCORRECT_DECREMENT": 0.10,
    "MASTERY_SPEED_BONUS_THRESHOLD_MS": 5000,
    "MASTERY_SPEED_BONUS": 0.05,
}


# =============================================================================
# NLP Pipeline Thresholds (Step 4)
# =============================================================================
NLP_THRESHOLDS: dict[str, float | int] = {
    # Sentiment analysis
    "SENTIMENT_FRUSTRATION_THRESHOLD": -0.30,     # polarity below = frustrated
    "SENTIMENT_CONFUSION_THRESHOLD": -0.10,       # mild negative = confused
    "SENTIMENT_POSITIVE_THRESHOLD": 0.30,          # polarity above = engaged/happy
    "SENTIMENT_WINDOW_SIZE": 5,                    # texts to average

    # Complexity analysis
    "COMPLEXITY_SIMPLE_THRESHOLD": 6.0,            # Flesch-Kincaid < 6 = simple
    "COMPLEXITY_MODERATE_THRESHOLD": 10.0,          # 6-10 = moderate
    "COMPLEXITY_HARD_THRESHOLD": 14.0,              # 10-14 = hard, >14 = very hard
    "COMPLEXITY_WORD_COUNT_MIN": 5,                 # min words for analysis

    # Keyword extraction
    "KEYWORD_MIN_FREQUENCY": 2,                    # min occurrences
    "KEYWORD_MAX_KEYWORDS": 10,                    # max keywords per text
    "KEYWORD_MIN_WORD_LENGTH": 3,                  # ignore short words

    # Answer quality
    "ANSWER_MIN_LENGTH_CHARS": 10,                 # too short = low effort
    "ANSWER_GOOD_LENGTH_CHARS": 50,                # decent answer
    "ANSWER_EXCELLENT_LENGTH_CHARS": 150,           # detailed answer
    "ANSWER_KEYWORD_OVERLAP_GOOD": 0.30,           # 30% concept keyword overlap
    "ANSWER_KEYWORD_OVERLAP_EXCELLENT": 0.60,      # 60% = excellent

    # Confusion detector
    "CONFUSION_HEDGE_WEIGHT": 0.3,                 # weight per hedge word
    "CONFUSION_QUESTION_WEIGHT": 0.2,              # weight per question mark
    "CONFUSION_NEGATION_WEIGHT": 0.15,             # weight per negation
    "CONFUSION_THRESHOLD": 0.50,                   # above = confused

    # Readability targets by grade
    "READABILITY_GRADE_6_MAX": 6.0,
    "READABILITY_GRADE_8_MAX": 8.0,
    "READABILITY_GRADE_10_MAX": 10.0,
    "READABILITY_GRADE_12_MAX": 12.0,

    # Topic drift
    "TOPIC_DRIFT_THRESHOLD": 0.40,                 # similarity below = drift
    "TOPIC_DRIFT_WINDOW_SIZE": 3,                  # recent texts to compare
}


# =============================================================================
# OpenAI / GPT-4 Configuration (Step 6)
# =============================================================================
OPENAI_CONFIG: dict[str, object] = {
    "API_KEY_ENV_VAR": "OPENAI_API_KEY",
    "MODEL_PRODUCTION": "gpt-4-turbo-preview",
    "MODEL_FALLBACK": "gpt-3.5-turbo",
    "MAX_TOKENS_PER_REQUEST": 200,
    "TEMPERATURE": 0.7,
    "TIMEOUT_SECONDS": 10,
    "MAX_RETRIES": 3,
}

INTERVENTION_COST_LIMITS: dict[str, float | int] = {
    "SESSION_LIMIT_USD": 5.00,
    "STUDENT_LIFETIME_LIMIT_USD": 50.00,
    "CACHE_MAX_SIZE": 10000,
    "CACHE_TTL_DAYS": 30,
    "RATE_LIMIT_PER_MINUTE": 60,
}


# =============================================================================
# Content Generation Pipeline (Step 7)
# =============================================================================
CONTENT_GENERATION_CONFIG: dict[str, object] = {
    # PDF Parsing
    "PDF_MAX_PAGES": 200,
    "PDF_MIN_TEXT_LENGTH": 50,
    "PDF_TABLE_STRATEGY": "text",           # pdfplumber table strategy

    # Concept Extraction (GPT-4)
    "CONCEPT_EXTRACTION_MODEL": "gpt-4-turbo-preview",
    "CONCEPT_EXTRACTION_MAX_TOKENS": 2000,
    "CONCEPT_EXTRACTION_TEMPERATURE": 0.3,
    "MAX_CONCEPTS_PER_CHUNK": 15,
    "CHUNK_SIZE_CHARS": 4000,
    "CHUNK_OVERLAP_CHARS": 200,

    # Slide Generation
    "SLIDES_MAX_PER_CONCEPT": 3,
    "SLIDES_FONT_SIZE_TITLE": 32,
    "SLIDES_FONT_SIZE_BODY": 18,
    "SLIDES_WIDTH_INCHES": 13.333,
    "SLIDES_HEIGHT_INCHES": 7.5,

    # Script / Narration
    "SCRIPT_MODEL": "gpt-4-turbo-preview",
    "SCRIPT_MAX_TOKENS": 1500,
    "SCRIPT_TEMPERATURE": 0.7,
    "TTS_MODEL": "tts-1",
    "TTS_VOICE": "alloy",
    "TTS_SPEED": 1.0,

    # Diagram (DALL-E)
    "DIAGRAM_MODEL": "dall-e-3",
    "DIAGRAM_SIZE": "1024x1024",
    "DIAGRAM_QUALITY": "standard",

    # Video Assembly
    "VIDEO_FPS": 24,
    "VIDEO_RESOLUTION": (1920, 1080),
    "VIDEO_CODEC": "libx264",
    "VIDEO_AUDIO_CODEC": "aac",
    "SLIDE_DURATION_SECONDS": 8,

    # Story Generation
    "STORY_MODEL": "gpt-4-turbo-preview",
    "STORY_MAX_TOKENS": 2000,
    "STORY_TEMPERATURE": 0.8,

    # Quiz Generation
    "QUIZ_MODEL": "gpt-4-turbo-preview",
    "QUIZ_MAX_TOKENS": 2000,
    "QUIZ_TEMPERATURE": 0.5,
    "QUIZ_QUESTIONS_PER_CONCEPT": 3,
    "QUIZ_DIFFICULTY_LEVELS": ["easy", "medium", "hard"],

    # Progress Tracking
    "PROGRESS_UPDATE_INTERVAL_SECONDS": 2,

    # Output directories (relative to PROJECT_ROOT)
    "OUTPUT_DIR": "output",
    "VIDEO_SUBDIR": "videos",
    "SLIDES_SUBDIR": "slides",
    "NOTES_SUBDIR": "notes",
    "QUIZ_SUBDIR": "quizzes",
}


# =============================================================================
# Spaced Repetition Engine (Step 8)
# =============================================================================
SPACED_REPETITION_CONFIG: dict[str, float | int | str] = {
    # Forgetting-curve fitting
    "DEFAULT_TAU_DAYS": 3.0,              # default decay constant when <3 data points
    "MIN_DATA_POINTS_FOR_FIT": 3,
    "TAU_LOWER_BOUND": 0.1,               # days
    "TAU_UPPER_BOUND": 30.0,              # days
    "CURVE_FIT_MAX_ITERATIONS": 5000,

    # Review scheduling
    "REVIEW_THRESHOLD": 0.70,             # schedule review before retention drops below this
    "SAFETY_BUFFER_DAYS": 1.0,            # review this many days BEFORE predicted threshold
    "FIRST_REVIEW_HOURS": 2,              # hours after mastery for 1st review

    # Timing
    "SLEEP_OBSERVATION_WINDOW_DAYS": 14,
    "DEFAULT_BEDTIME_HOUR": 22.0,         # 10 PM
    "SLEEP_WINDOW_MINUTES_BEFORE": 60,
    "CIRCADIAN_MIN_SESSIONS": 20,
    "CIRCADIAN_DEFAULT_PEAK_START": 14.0,  # 2 PM
    "CIRCADIAN_DEFAULT_PEAK_END": 17.0,    # 5 PM
    "CIRCADIAN_WINDOW_HOURS": 3,

    # Quiz generation
    "QUIZ_QUESTIONS_PER_REVIEW": 3,
    "QUIZ_SECONDS_PER_QUESTION": 60,

    # Sleep-window eligibility
    "SLEEP_MASTERY_LOW": 0.60,
    "SLEEP_MASTERY_HIGH": 0.85,

    # Notifications
    "NOTIFICATION_TITLE": "NeuroSync Review",
    "NOTIFICATION_TIMEOUT_SECONDS": 30,
}

# =============================================================================
# Pre-Lesson Readiness Protocol (Step 9)
# =============================================================================
READINESS_CONFIG: dict[str, float | int | str | list[str]] = {
    # Self-report assessment
    "SELF_REPORT_QUESTIONS": 3,           # familiarity, difficulty_perception, emotional_state

    # Physiological assessment — blink rate norms (blinks/min)
    "BLINK_RATE_LOW": 12.0,               # below = very calm
    "BLINK_RATE_NORMAL_HIGH": 20.0,       # 12-20 = normal
    "BLINK_RATE_ELEVATED": 25.0,          # 20-25 = mildly elevated
    # >25 scales linearly toward 1.0 anxiety (capped at 40 bpm)
    "BLINK_RATE_ANXIETY_CAP": 40.0,

    # Behavioral warmup assessment
    "WARMUP_QUESTIONS": 3,
    "RESPONSE_TIME_NORM_SECONDS": 8.0,    # expected mean response time
    "RESPONSE_TIME_SLOW_SECONDS": 15.0,   # clearly slow / distracted
    "CV_THRESHOLD": 0.50,                 # coefficient of variation threshold

    # Readiness scoring weights (must sum to 1.0)
    "WEIGHT_SELF_REPORT": 0.50,
    "WEIGHT_PHYSIOLOGICAL": 0.30,
    "WEIGHT_BEHAVIORAL": 0.20,

    # Thresholds
    "READY_THRESHOLD": 0.60,              # readiness >= this → proceed
    "ANXIETY_HIGH_THRESHOLD": 0.65,       # anxiety >= this → offer breathing

    # Breathing exercise timing (seconds)
    "BREATHE_INHALE": 4.0,
    "BREATHE_HOLD": 4.0,
    "BREATHE_EXHALE": 6.0,
    "BREATHE_CYCLES": 8,
    # total = (4+4+6) * 8 = 112 seconds

    # Post-intervention
    "RECHECK_AFTER_BREATHING": True,
    "MAX_RECHECKS": 1,
}


def get_threshold(key: str) -> float:
    """Get a threshold value by key, raising KeyError if not found."""
    for source in (BEHAVIORAL_THRESHOLDS, WEBCAM_THRESHOLDS, KNOWLEDGE_THRESHOLDS, NLP_THRESHOLDS):
        value = source.get(key)
        if value is not None:
            return float(value)
    raise KeyError(key)


# =============================================================================
# LLM Provider Configuration (Step 13 - Free Migration)
# =============================================================================
LLM_CONFIG: dict[str, object] = {
    "PROVIDER": os.getenv("LLM_PROVIDER", "groq"),
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    "GROQ_MODEL": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o"),
}

# =============================================================================
# TTS Provider Configuration (Step 13 - Free Migration)
# =============================================================================
TTS_CONFIG: dict[str, object] = {
    "PROVIDER": os.getenv("TTS_PROVIDER", "gtts"),
    "LANGUAGE": os.getenv("TTS_LANGUAGE", "en"),
    "VOICE_SPEED": os.getenv("TTS_VOICE_SPEED", "normal"),
}


def get_llm_provider():
    """Get configured LLM provider via factory."""
    from neurosync.llm.factory import LLMProviderFactory

    return LLMProviderFactory.create_provider()


def get_tts_provider():
    """Get configured TTS provider via factory."""
    from neurosync.tts.factory import TTSProviderFactory

    return TTSProviderFactory.create_provider()
