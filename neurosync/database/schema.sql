-- NeuroSync AI — Complete database schema (SQLite)
-- Created for Step 1: Behavioral Signal Collector

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    started_at REAL NOT NULL,
    ended_at REAL,
    eeg_enabled INTEGER DEFAULT 0,
    webcam_enabled INTEGER DEFAULT 0,
    experiment_group TEXT,
    total_duration_ms REAL,
    completion_percentage REAL,
    created_at REAL DEFAULT (unixepoch('now', 'subsec'))
);

-- Raw events table (high-frequency, optimised for append)
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    event_type TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Computed signal snapshots (one row per fusion cycle)
CREATE TABLE IF NOT EXISTS signal_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    -- Behavioral signals
    response_time_mean_ms REAL,
    response_time_trend TEXT,
    fast_answer_rate REAL,
    rewinds_per_minute REAL,
    rewind_burst INTEGER DEFAULT 0,
    idle_frequency REAL,
    interaction_variance REAL,
    scroll_pattern TEXT,
    -- Moment scores
    frustration_score REAL,
    fatigue_score REAL,
    -- Webcam signals (null until Step 2)
    gaze_off_screen INTEGER,
    blink_rate REAL,
    facial_tension REAL,
    -- EEG signals (null until Step 10)
    alpha_power REAL,
    beta_power REAL,
    theta_power REAL,
    -- Active moments
    active_moments TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Question attempts (for M04, M14, M17)
CREATE TABLE IF NOT EXISTS question_attempts (
    attempt_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    answer_given TEXT,
    answer_correct INTEGER,
    response_time_ms REAL,
    confidence_score INTEGER,
    attempt_number INTEGER DEFAULT 1,
    authenticity_score REAL,
    mastery_flag TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Interventions fired
CREATE TABLE IF NOT EXISTS interventions (
    intervention_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    moment_id TEXT NOT NULL,
    intervention_type TEXT NOT NULL,
    urgency TEXT NOT NULL,
    payload TEXT,
    confidence REAL,
    signals_triggered TEXT,
    student_acknowledged INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Mastery records (for M04, M17 spaced repetition)
CREATE TABLE IF NOT EXISTS mastery_records (
    record_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    first_mastered_at REAL,
    last_tested_at REAL,
    authenticity_score REAL,
    next_review_at REAL,
    review_count INTEGER DEFAULT 0,
    retention_history TEXT,
    UNIQUE(student_id, concept_id)
);

-- Session performance summary (for M12 circadian profiling)
CREATE TABLE IF NOT EXISTS session_summaries (
    summary_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    student_id TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    start_time_of_day REAL,
    duration_minutes REAL,
    concepts_encountered INTEGER,
    concepts_mastered INTEGER,
    quiz_score_percentage REAL,
    completion_percentage REAL,
    average_frustration_score REAL,
    average_fatigue_score REAL,
    intervention_count INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_snapshots_session ON signal_snapshots(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_attempts_student ON question_attempts(student_id, concept_id);
CREATE INDEX IF NOT EXISTS idx_mastery_student ON mastery_records(student_id, next_review_at);
CREATE INDEX IF NOT EXISTS idx_summaries_student ON session_summaries(student_id, start_time_of_day);
