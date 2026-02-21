# NeuroSync-AI Implementation Report

> **Project:** NeuroSync-AI — AI-Powered Adaptive Learning System  
> **Repository:** [Sabarish-29/NeuroSync-AI](https://github.com/Sabarish-29/NeuroSync-AI)  
> **Report Generated:** February 20, 2026  
> **Total Tests:** 285 (all passing)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Step 1: Project Foundation + Behavioral Signal Collector](#step-1-project-foundation--behavioral-signal-collector)
3. [Step 2: Webcam Gaze + Expression Detection Layer](#step-2-webcam-gaze--expression-detection-layer)
4. [Step 3: Knowledge Graph Layer with Neo4j](#step-3-knowledge-graph-layer-with-neo4j)
5. [Step 4: NLP Pipeline](#step-4-nlp-pipeline)
6. [Step 5: LangGraph Fusion Engine](#step-5-langgraph-fusion-engine)
7. [Step 6: GPT-4 Intervention Engine](#step-6-gpt-4-intervention-engine)
8. [Step 7: Content Generation Pipeline](#step-7-content-generation-pipeline)
9. [Step 8: Spaced Repetition Engine](#step-8-spaced-repetition-engine)
10. [Step 9: Pre-Lesson Readiness Protocol](#step-9-pre-lesson-readiness-protocol)
11. [Step 10: EEG Integration (Planned)](#step-10-eeg-integration-planned)
12. [Architecture Overview](#architecture-overview)
13. [Test Coverage Summary](#test-coverage-summary)
14. [Dependencies](#dependencies)

---

## Executive Summary

NeuroSync-AI is an intelligent tutoring system that detects **22 learning failure moments** (M01-M22) in real-time and delivers personalized interventions. The system integrates:

- **Behavioral analytics** from user interactions
- **Computer vision** for gaze, expression, and physiological signals
- **Knowledge graphs** for concept mastery tracking
- **NLP** for answer quality and confusion detection
- **LLM-powered interventions** via GPT-4
- **Spaced repetition** with personalized forgetting curves
- **Pre-lesson readiness assessment** with anxiety interventions

### Implementation Status

| Step | Feature | Status | Tests |
|------|---------|--------|-------|
| 1 | Project Foundation + Behavioral Collector | ✅ Complete | 41 |
| 2 | Webcam Gaze + Expression Detection | ✅ Complete | 20 |
| 3 | Knowledge Graph (Neo4j) | ✅ Complete | 43 |
| 4 | NLP Pipeline | ✅ Complete | 39 |
| 5 | LangGraph Fusion Engine | ✅ Complete | 33 |
| 6 | GPT-4 Intervention Engine | ✅ Complete | 24 |
| 7 | Content Generation Pipeline | ✅ Complete | 42 |
| 8 | Spaced Repetition Engine | ✅ Complete | 22 |
| 9 | Pre-Lesson Readiness Protocol | ✅ Complete | 18 |
| 10 | EEG Integration | 🔲 Planned | - |

---

## Step 1: Project Foundation + Behavioral Signal Collector

**Commit:** `54a6fa2`  
**Tests Added:** 41  
**Description:** Established the core architecture, event system, database layer, and behavioral signal processing.

### 1.1 Configuration System

**File:** `neurosync/config/settings.py`

- Pydantic v2 models for type-safe configuration
- 27+ configurable thresholds for all signal processors
- Environment variable support for sensitive values

```python
# Example threshold configuration
THRESHOLDS = {
    "RESPONSE_TIME_WINDOW": 10,
    "FAST_ANSWER_THRESHOLD_MS": 2000,
    "FRUSTRATION_WATCH_THRESHOLD": 0.3,
    "FRUSTRATION_WARNING_THRESHOLD": 0.5,
    "FRUSTRATION_CRITICAL_THRESHOLD": 0.7,
    ...
}
```

### 1.2 Core Event Types

**File:** `neurosync/core/events.py`

All system events are modeled with Pydantic v2 for validation:

| Event Type | Description | Key Fields |
|------------|-------------|------------|
| `RawEvent` | Base event model | `event_id`, `session_id`, `student_id`, `timestamp`, `event_type` |
| `QuestionEvent` | Question interactions | `question_id`, `concept_id`, `answer_correct`, `response_time_ms`, `confidence_score` |
| `VideoEvent` | Video playback | `video_id`, `playback_position_ms`, `playback_speed`, `seek_from_ms`, `seek_to_ms` |
| `IdleEvent` | Idle periods | `idle_duration_ms`, `preceding_event_type` |
| `TextEvent` | Student text input | `text`, `context`, `expected_keywords` |
| `SessionConfig` | Session metadata | `session_id`, `student_id`, `lesson_id`, `eeg_enabled`, `webcam_enabled` |

### 1.3 The 22 Learning Failure Moments

**File:** `neurosync/core/constants.py`

The system is built around detecting 22 specific learning failure moments:

| ID | Moment | Description |
|----|--------|-------------|
| M01 | Attention Drop | Student's attention wanders from content |
| M02 | Cognitive Overload | Content complexity exceeds processing capacity |
| M03 | Knowledge Gap | Missing prerequisite knowledge detected |
| M04 | Mastery Verification | Need to verify authentic understanding |
| M05 | Pre-Lesson Anxiety | Anxiety before lesson begins |
| M06 | Stealth Boredom | Hidden boredom not overtly expressed |
| M07 | Silent Frustration | Frustration building toward dropout |
| M08 | Insight Moment | "Aha!" breakthrough opportunity |
| M09 | Confidence Collapse | Sudden loss of confidence |
| M10 | Mental Fatigue | Cognitive exhaustion from prolonged effort |
| M11 | Physical Discomfort | Posture/environmental discomfort |
| M12 | Circadian Peak | Optimal learning window |
| M13 | Wrong Method | Learning approach mismatch |
| M14 | Pseudo-Understanding | False sense of mastery |
| M15 | Misconception | Active incorrect mental model |
| M16 | Working Memory Overflow | Too many items in working memory |
| M17 | Forgetting Curve | Previously learned content fading |
| M18 | Transfer Failure | Cannot apply knowledge to new contexts |
| M19 | Sleep Window | Optimal sleep consolidation timing |
| M20 | Dopamine Crash | Reward system fatigue |
| M21 | Interruption | External distraction detected |
| M22 | Plateau Escape | Learning progress stalled |

### 1.4 SQLite Database Layer

**File:** `neurosync/database/manager.py`

Thread-safe SQLite database with WAL mode:

```python
class DatabaseManager:
    """SQLite manager with WAL mode for concurrent read/write."""
    
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._local = threading.local()  # Thread-local connections
        self._lock = threading.Lock()
        
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
```

**Database Tables (7 total):**

| Table | Purpose |
|-------|---------|
| `sessions` | Learning session records |
| `events` | Raw event storage |
| `signals` | Processed signal snapshots |
| `mastery_records` | Student-concept mastery |
| `interventions` | Delivered intervention log |
| `intervention_cache` | LLM response cache |
| `readiness_checks` | Pre-lesson readiness results |

**Repository Pattern:**

- `SessionRepository` — Session CRUD operations
- `EventRepository` — Event persistence and queries
- `SignalRepository` — Signal snapshot storage

### 1.5 Async Event Collector

**File:** `neurosync/behavioral/collector.py`

```python
class AsyncEventCollector:
    """
    Validates, persists, and dispatches events to signal processors.
    
    Flow: Event arrives → validate (Pydantic) → write to SQLite →
          push to asyncio.Queue → signal processors consume from queue
    """
    
    async def record_event(self, event: RawEvent) -> None:
        """Validate, persist, and dispatch a raw event."""
        event.session_id = self._config.session_id
        self._event_repo.insert_event(event)
        await self._queue.put(event)
        
    async def record_question(self, event: QuestionEvent) -> None:
        """Specialized handler for question events."""
        ...
        
    async def record_video_event(self, event: VideoEvent) -> None:
        """Specialized handler for video events."""
        ...
```

### 1.6 Behavioral Signal Processors

**File:** `neurosync/behavioral/signals.py`

All processors follow the `SignalProcessor` protocol for extensibility:

```python
@runtime_checkable
class SignalProcessor(Protocol):
    def process(self, events: list[RawEvent]) -> SignalResult: ...
    def get_current_value(self) -> dict[str, float]: ...
    def reset(self) -> None: ...
```

#### ResponseTimeSignal

Tracks question response times to detect patterns:

- **Window:** Last N questions (default: 10)
- **Outputs:** Mean response time, trend (stable/increasing/decreasing), fast answer rate
- **Use Case:** Detecting guessing (fast answers) or struggling (slow answers)

```python
class ResponseTimeSignal:
    def process(self, events: list[RawEvent]) -> ResponseTimeResult:
        # Computes mean, trend via linear regression, fast answer percentage
        ...
```

#### RewindSignal

Detects video rewind bursts indicating confusion:

- **Burst Detection:** 3+ rewinds within 60 seconds
- **Segment Tracking:** Identifies repeatedly rewound video segments
- **Use Case:** Detecting frustration (M07), knowledge gaps (M03)

#### IdleSignal

Monitors idle periods during learning:

- **Micro-idle:** < 30 seconds (normal pauses)
- **Macro-idle:** > 30 seconds (potential disengagement)
- **Trend Analysis:** Idle duration trend over session

#### InteractionVarianceSignal

Tracks variation in interaction patterns:

- **Variance Computation:** Rolling variance of interaction timing
- **Stability Detection:** High variance = erratic behavior
- **Use Case:** Detecting fatigue (M10), frustration (M07)

#### ScrollSignal

Analyzes scroll behavior patterns:

- **States:** Engaged (slow, deliberate), Skimming (medium), Rushing (fast)
- **Direction Tracking:** Up/down scroll patterns
- **Use Case:** Detecting boredom (M06), cognitive overload (M02)

#### SessionPacingSignal

Monitors overall session pacing:

- **Time-on-task:** Total engaged time
- **Break Detection:** Optimal break timing
- **Fatigue Prediction:** Based on session duration

### 1.7 Moment Detectors

**File:** `neurosync/behavioral/moments.py`

#### FrustrationDetector (M07)

Composite frustration score predicting dropout risk:

```python
class FrustrationDetector:
    def detect(
        self,
        rewind_burst: bool = False,
        response_time_trend: str = "stable",
        idle_trend: str = "stable",
        facial_tension: float = 0.0,      # From Step 2
        eeg_theta_high: float = 0.0,      # From Step 10
    ) -> FrustrationResult:
        score = (
            rewind_burst * 0.30 +
            response_time_increasing * 0.25 +
            idle_increasing * 0.20 +
            facial_tension * 0.15 +
            eeg_theta_high * 0.10
        )
        # Returns level: none/watch/warning/critical
```

#### FatigueDetector (M10)

Tracks mental fatigue from interaction variance:

- **Indicators:** Response time degradation, interaction variance increase
- **Levels:** Fresh → Mild → Tired → Critical
- **Intervention:** Suggests breaks, reduces content complexity

#### PseudoUnderstandingDetector (M14)

Detects false confidence:

- **Pattern:** Fast correct answers + low self-reported confidence
- **Response:** Triggers verification questions
- **Output:** `MasteryCheckResult` with authenticity score

#### InsightDetector (M08)

Behavioral proxy for "aha!" moments:

- **Indicators:** Sudden response time improvement, increased confidence
- **Opportunity:** Reinforce learning at peak engagement

#### VariableRewardManager (M20)

Prevents dopamine crash from reward fatigue:

- **Strategy:** Variable ratio reward schedule
- **Types:** Points, badges, streak bonuses, surprise rewards
- **Cooldown:** Prevents over-rewarding

### 1.8 Behavioral Fusion Engine

**File:** `neurosync/behavioral/fusion.py`

Coordinates all behavioral signal processors:

```python
class BehavioralFusionEngine:
    def __init__(self):
        self._response_time = ResponseTimeSignal()
        self._rewind = RewindSignal()
        self._idle = IdleSignal()
        self._variance = InteractionVarianceSignal()
        self._scroll = ScrollSignal()
        self._pacing = SessionPacingSignal()
        
    def process_events(self, events: list[RawEvent]) -> BehavioralSnapshot:
        """Run all processors and return unified snapshot."""
        ...
```

---

## Step 2: Webcam Gaze + Expression Detection Layer

**Commit:** `7f18088`  
**Tests Added:** 20 (Total: 61)  
**Description:** Computer vision layer for gaze tracking, expression recognition, and physiological signals.

### 2.1 MediaPipe Integration

**File:** `neurosync/webcam/mediapipe_processor.py`

Uses Google MediaPipe for face and pose landmarks:

```python
@dataclass
class RawLandmarks:
    """Output from MediaPipe processing."""
    frame_timestamp: float
    face_detected: bool
    face_landmarks: np.ndarray | None      # 478 points
    pose_landmarks: np.ndarray | None      # 33 points
    left_iris: np.ndarray | None
    right_iris: np.ndarray | None
    
class MediaPipeProcessor:
    def __init__(self):
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,  # Enables iris tracking
            min_detection_confidence=0.5,
        )
        self._pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.5,
        )
```

### 2.2 Thread-Safe Webcam Capture

**File:** `neurosync/webcam/capture.py`

Background capture with daemon thread:

```python
class WebcamCapture:
    """Thread-safe webcam capture with background daemon."""
    
    def __init__(self, camera_id: int = 0, fps: int = 30):
        self._cap = cv2.VideoCapture(camera_id)
        self._frame_queue = queue.Queue(maxsize=2)
        self._daemon_thread = threading.Thread(target=self._capture_loop, daemon=True)
        
    def get_frame(self) -> np.ndarray | None:
        """Get latest frame (non-blocking)."""
        ...
```

### 2.3 Five Signal Processors

**Directory:** `neurosync/webcam/signals/`

#### GazeSignal (`gaze.py`)

Iris-ratio based gaze direction detection:

```python
@dataclass
class GazeResult:
    direction: Literal["center", "left", "right", "up", "down"]
    on_screen: bool
    confidence: float
    off_screen_duration_ms: float

class GazeSignal:
    """
    Computes gaze direction from iris position relative to eye corners.
    Uses rolling majority vote to smooth noisy detections.
    """
    def process(self, landmarks: RawLandmarks) -> GazeResult:
        # Calculate iris position ratio
        # Apply majority vote over last 5 frames
        ...
```

#### BlinkSignal (`blink.py`)

EAR (Eye Aspect Ratio) based blink detection:

```python
@dataclass
class BlinkResult:
    blink_detected: bool
    blink_rate_per_minute: float
    fatigue_indicator: bool      # High blink rate
    anxiety_indicator: bool      # Very high blink rate
    flow_indicator: bool         # Reduced blink rate (deep focus)

class BlinkSignal:
    """
    EAR formula: (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
    Blink detected when EAR < threshold for consecutive frames.
    """
    def __init__(self):
        self._window = deque(maxlen=1800)  # 60 seconds at 30 fps
        self._ear_threshold = 0.21
```

**Blink Rate Interpretation:**

| Rate (blinks/min) | State | Moment |
|-------------------|-------|--------|
| < 10 | Flow/Deep Focus | (positive) |
| 10-20 | Normal | - |
| 20-30 | Mild Fatigue | M10 |
| 30-40 | Anxiety | M07 boost |
| > 40 | High Stress | M07 critical |

#### ExpressionSignal (`expression.py`)

Geometric ratio classifier for facial expressions:

```python
@dataclass
class ExpressionResult:
    dominant_expression: str          # neutral/happy/confused/frustrated/bored
    boredom_indicator: float          # 0.0 - 1.0
    frustration_tension: float        # 0.0 - 1.0
    engagement_score: float           # 0.0 - 1.0

class ExpressionSignal:
    """
    Uses facial landmark ratios:
    - Mouth aspect ratio (MAR)
    - Eyebrow height ratio
    - Eye openness ratio
    - Lip corner angle
    
    Applies EMA smoothing to reduce noise.
    """
```

**Expression Indicators:**

| Expression | Key Ratios | Learning Moment |
|------------|------------|-----------------|
| Confused | Raised eyebrows, squinted eyes | M03, M15 |
| Frustrated | Furrowed brow, tight lips | M07 |
| Bored | Relaxed face, drooping eyelids | M06 |
| Engaged | Slight forward lean, focused eyes | (positive) |

#### PoseSignal (`pose.py`)

Head and shoulder posture analysis:

```python
@dataclass
class PoseResult:
    head_position: Literal["upright", "tilted", "drooping"]
    shoulder_state: Literal["relaxed", "raised", "hunched"]
    fidget_detected: bool
    physical_discomfort_probability: float

class PoseSignal:
    """
    Tracks:
    - Head pose (yaw, pitch, roll)
    - Shoulder elevation relative to ears
    - Movement variance (fidgeting)
    """
    def __init__(self):
        self._position_history = deque(maxlen=150)  # 5 seconds at 30 fps
```

#### RemotePPGSignal (`rppg.py`)

Heart rate estimation from facial video:

```python
@dataclass
class RPPGResult:
    heart_rate_bpm: float | None
    heart_rate_confidence: float
    stress_indicator: bool           # HR > baseline + threshold
    signal_quality: float

class RemotePPGSignal:
    """
    Remote photoplethysmography using green channel from forehead region.
    
    Algorithm:
    1. Extract forehead ROI from landmarks
    2. Compute spatial average of green channel
    3. Apply bandpass filter (0.7-4 Hz)
    4. Find dominant frequency via FFT
    5. Convert to BPM
    """
```

### 2.4 Webcam Fusion Engine

**File:** `neurosync/webcam/fusion.py`

Combines all 5 signals into moment-relevant scores:

```python
@dataclass
class WebcamMomentScores:
    timestamp: float
    attention_score: float           # M01 - from gaze + expression
    off_screen_triggered: bool
    off_screen_duration_ms: float
    frustration_boost: float         # M07 boost - from expression + pose
    boredom_score: float             # M06 - from expression + blink
    discomfort_probability: float    # M11 - from pose + rPPG
    fatigue_boost: float             # M10 boost - from blink + pose
    heart_rate_bpm: float | None
    face_detected: bool
    signal_quality_overall: float

class WebcamFusionEngine:
    def compute(self, landmarks: RawLandmarks, frame: np.ndarray) -> WebcamMomentScores:
        gaze_r = self._gaze.process(landmarks)
        blink_r = self._blink.process(landmarks)
        expr_r = self._expression.process(landmarks)
        pose_r = self._pose.process(landmarks)
        rppg_r = self._rppg.process(landmarks, frame=frame)
        
        return self._fuse(gaze_r, blink_r, expr_r, pose_r, rppg_r)
```

**Fusion Weights:**

```python
# ATTENTION (M01)
attention = (
    on_screen * 0.60 +
    (1 - boredom_indicator) * 0.25 +
    (1 - fatigue_indicator) * 0.15
)

# FRUSTRATION BOOST (M07)
frustration_boost = (
    expression_tension * 0.60 +
    shoulder_raised * 0.25 +
    anxiety_indicator * 0.15
)

# BOREDOM (M06)
boredom = (
    boredom_indicator * 0.40 +
    (1 - flow_indicator) * 0.30 +
    head_drooping * 0.30
)
```

### 2.5 Webcam Signal Injector

**File:** `neurosync/webcam/injector.py`

Bridges webcam data to the behavioral collector:

```python
class WebcamSignalInjector:
    """Injects webcam scores into the Step 1 signal snapshot."""
    
    def inject(self, collector: AsyncEventCollector, scores: WebcamMomentScores) -> None:
        collector.inject_webcam_signal(scores)
```

### 2.6 Configuration

**Added to `settings.py`:** 27 webcam-specific thresholds:

```python
WEBCAM_THRESHOLDS = {
    "GAZE_ON_SCREEN_RATIO": 0.7,
    "BLINK_FATIGUE_THRESHOLD": 25,
    "BLINK_ANXIETY_THRESHOLD": 35,
    "BLINK_FLOW_THRESHOLD": 8,
    "EAR_THRESHOLD": 0.21,
    "EXPRESSION_EMA_ALPHA": 0.3,
    "RPPG_BUFFER_SECONDS": 10,
    "RPPG_MIN_CONFIDENCE": 0.6,
    ...
}
```

---

## Step 3: Knowledge Graph Layer with Neo4j

**Commit:** `2ccc0bd`  
**Tests Added:** 43 (Total: 104)  
**Description:** Neo4j-based knowledge graph for concept relationships, mastery tracking, and learning analytics.

### 3.1 Neo4j Graph Manager

**File:** `neurosync/knowledge/graph_manager.py`

Connection manager with graceful degradation:

```python
class GraphManager:
    """
    Neo4j connection manager with automatic retry and graceful degradation.
    When Neo4j is unavailable, methods return safe defaults.
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self._uri = uri or NEO4J_CONFIG["URI"]
        self._retry_attempts = 3
        self._retry_delay = 1.0
        
    def connect(self) -> bool:
        """Establish connection with retry logic."""
        for attempt in range(self._retry_attempts):
            try:
                self._driver = GraphDatabase.driver(self._uri, auth=(user, password))
                self._driver.verify_connectivity()
                return True
            except Exception:
                time.sleep(self._retry_delay)
        return False  # Graceful degradation
        
    def session(self) -> Session:
        """Create a Neo4j session (or mock session in offline mode)."""
        ...
```

### 3.2 Graph Schema

**File:** `neurosync/knowledge/schema.cypher`

```cypher
// Concept nodes
CREATE CONSTRAINT concept_id IF NOT EXISTS
FOR (c:Concept) REQUIRE c.concept_id IS UNIQUE;

// Student nodes
CREATE CONSTRAINT student_id IF NOT EXISTS
FOR (s:Student) REQUIRE s.student_id IS UNIQUE;

// Relationships
// (:Concept)-[:PREREQUISITE_OF]->(:Concept)
// (:Concept)-[:RELATED_TO]->(:Concept)
// (:Student)-[:MASTERED {score, timestamp, authenticity}]->(:Concept)
// (:Student)-[:HAS_MISCONCEPTION {description, detected_at}]->(:Concept)
```

### 3.3 Six Detectors

**Directory:** `neurosync/knowledge/detectors/`

#### GapDetector (`gap_detector.py`)

Identifies missing prerequisite concepts:

```python
class GapDetector:
    """
    Finds knowledge gaps by traversing prerequisite graph.
    
    Algorithm:
    1. Get current concept's prerequisites
    2. Check student's mastery of each prerequisite
    3. Return unmastered prerequisites sorted by depth
    """
    
    def detect_gaps(self, student_id: str, concept_id: str) -> list[KnowledgeGap]:
        prerequisites = self._get_prerequisites(concept_id, max_depth=3)
        mastered = self._get_mastered_concepts(student_id)
        return [p for p in prerequisites if p not in mastered]
```

#### MasteryChecker (`mastery_checker.py`)

Verifies authentic vs. surface understanding:

```python
class MasteryChecker:
    """
    Determines if mastery is authentic or pseudo-understanding.
    
    Factors:
    - Response time patterns (too fast = guessing)
    - Confidence calibration (confidence vs. correctness)
    - Transfer success (can apply to new contexts)
    - Retention over time
    """
    
    def check_mastery(self, student_id: str, concept_id: str) -> MasteryCheckResult:
        # Returns: authentic, suspicious, or unverified
        ...
```

#### MisconceptionDetector (`misconception_detector.py`)

Flags common misconceptions based on answer patterns:

```python
class MisconceptionDetector:
    """
    Detects misconceptions from wrong answer patterns.
    
    Uses a misconception database mapping:
    - Concept → Common misconceptions
    - Wrong answer patterns → Specific misconception
    """
    
    def detect(self, student_id: str, concept_id: str, 
               wrong_answers: list[str]) -> list[Misconception]:
        # Pattern matching against known misconceptions
        ...
```

#### PlateauDetector (`plateau_detector.py`)

Detects learning plateaus from progress curves:

```python
class PlateauDetector:
    """
    Identifies when learning progress has stalled.
    
    Indicators:
    - Score variance below threshold for N attempts
    - No new concepts mastered in time window
    - Repeated errors on same question types
    """
    
    def detect_plateau(self, student_id: str) -> PlateauResult:
        # Returns: plateau_detected, duration, suggested_intervention
        ...
```

#### MirrorDetector (`mirror.py`)

Identifies concept confusion (mixing up similar concepts):

```python
class MirrorDetector:
    """
    Detects when student confuses similar concepts.
    
    Example: Confusing mitosis/meiosis, speed/velocity, mass/weight
    """
    
    def detect_confusion(self, student_id: str, 
                         answer: str, correct_concept: str) -> MirrorConfusion | None:
        related = self._get_related_concepts(correct_concept)
        # Check if answer matches a related concept instead
        ...
```

#### ChunkTracker (`chunk_tracker.py`)

Monitors working memory load:

```python
class ChunkTracker:
    """
    Tracks cognitive load based on active concepts.
    
    Working memory limit: ~4 chunks
    Warns when too many new concepts introduced without consolidation.
    """
    
    def track(self, student_id: str, active_concepts: list[str]) -> ChunkStatus:
        # Returns: load_level, overload_risk, consolidation_needed
        ...
```

### 3.4 Four Repositories

**Directory:** `neurosync/knowledge/repositories/`

#### ConceptRepository (`concepts.py`)

```python
class ConceptRepository:
    def create_concept(self, concept_id: str, name: str, 
                       subject: str, difficulty: float) -> None: ...
    def get_concept(self, concept_id: str) -> Concept | None: ...
    def get_prerequisites(self, concept_id: str) -> list[Concept]: ...
    def get_related_concepts(self, concept_id: str) -> list[Concept]: ...
    def add_prerequisite(self, concept_id: str, prereq_id: str) -> None: ...
```

#### MasteryRepository (`mastery.py`)

```python
class MasteryRepository:
    def record_mastery(self, student_id: str, concept_id: str, 
                       score: float, authenticity: float) -> None: ...
    def get_mastery(self, student_id: str, concept_id: str) -> Mastery | None: ...
    def get_all_mastered(self, student_id: str) -> list[Mastery]: ...
    def update_mastery(self, student_id: str, concept_id: str, 
                       new_score: float) -> None: ...
```

#### MisconceptionRepository (`misconceptions.py`)

```python
class MisconceptionRepository:
    def record_misconception(self, student_id: str, concept_id: str,
                             description: str) -> None: ...
    def get_misconceptions(self, student_id: str) -> list[Misconception]: ...
    def clear_misconception(self, student_id: str, concept_id: str) -> None: ...
```

#### StudentRepository (`students.py`)

```python
class StudentRepository:
    def create_student(self, student_id: str, name: str) -> None: ...
    def get_student(self, student_id: str) -> Student | None: ...
    def get_learning_history(self, student_id: str) -> LearningHistory: ...
```

### 3.5 Seeders

**Directory:** `neurosync/knowledge/seeders/`

Pre-populates the graph with:
- High school STEM concept hierarchies (Math, Physics, Chemistry, Biology)
- Prerequisite relationships
- Common misconception patterns

---

## Step 4: NLP Pipeline

**Commit:** `be8141d`  
**Tests Added:** 39 (Total: 143)  
**Description:** Natural language processing for student response analysis.

### 4.1 NLP Pipeline Orchestrator

**File:** `neurosync/nlp/pipeline.py`

```python
class NLPPipeline:
    """
    Orchestrates all NLP processors to produce a unified NLPResult.
    """
    
    def __init__(self):
        self._sentiment = SentimentAnalyzer()
        self._complexity = ComplexityAnalyzer()
        self._keywords = KeywordExtractor()
        self._answer_quality = AnswerQualityAssessor()
        self._confusion = ConfusionDetector()
        self._readability = ReadabilityAnalyzer()
        self._topic_drift = TopicDriftDetector()
        
    def analyze(self, text: str, 
                expected_keywords: list[str] = None,
                reference_keywords: list[str] = None) -> NLPResult:
        """Run all processors on student text."""
        sentiment = self._sentiment.analyze(text)
        complexity = self._complexity.analyze(text)
        keywords = self._keywords.extract(text)
        quality = self._answer_quality.assess(text, expected_keywords)
        confusion = self._confusion.detect(text)
        drift = self._topic_drift.check(text, reference_keywords)
        
        return NLPResult(
            sentiment_polarity=sentiment.polarity,
            sentiment_label=sentiment.label,
            complexity_score=complexity.score,
            complexity_label=complexity.label,
            confusion_score=confusion.score,
            confusion_label=confusion.label,
            answer_quality=quality.quality,
            keywords=keywords.keywords,
            topic_drift_detected=drift.drift_detected,
            ...
        )
```

### 4.2 Seven Processors

**Directory:** `neurosync/nlp/processors/`

#### SentimentAnalyzer (`sentiment.py`)

TextBlob-based sentiment analysis:

```python
class SentimentAnalyzer:
    """
    Analyzes emotional tone in student responses.
    
    Output:
    - polarity: -1.0 (negative) to 1.0 (positive)
    - subjectivity: 0.0 (objective) to 1.0 (subjective)
    - label: positive/neutral/negative
    """
```

**Use Cases:**
- Detecting frustration in free-text responses
- Identifying confidence level from language
- Tracking emotional trajectory over session

#### ComplexityAnalyzer (`complexity.py`)

Flesch-Kincaid based complexity assessment:

```python
class ComplexityAnalyzer:
    """
    Measures linguistic complexity of student writing.
    
    Metrics:
    - Flesch-Kincaid Grade Level
    - Average sentence length
    - Syllables per word
    - Vocabulary sophistication
    """
    
    def analyze(self, text: str) -> ComplexityResult:
        fk_grade = textstat.flesch_kincaid_grade(text)
        return ComplexityResult(
            score=fk_grade,
            label=self._grade_to_label(fk_grade),
            word_count=len(text.split()),
            ...
        )
```

#### KeywordExtractor (`keywords.py`)

TF-IDF based keyword extraction:

```python
class KeywordExtractor:
    """
    Extracts key concepts from student responses.
    
    Uses TF-IDF with domain-specific stop words.
    """
    
    def extract(self, text: str, top_n: int = 5) -> KeywordResult:
        # Returns ranked list of keywords with scores
        ...
```

#### AnswerQualityAssessor (`answer_quality.py`)

Evaluates answer completeness:

```python
class AnswerQualityAssessor:
    """
    Assesses answer quality based on:
    - Keyword overlap with expected concepts
    - Completeness of explanation
    - Use of domain vocabulary
    """
    
    def assess(self, answer: str, expected_keywords: list[str]) -> QualityResult:
        overlap = self._compute_overlap(answer, expected_keywords)
        return QualityResult(
            quality="complete" | "partial" | "incomplete" | "off_topic",
            score=overlap,
            missing_keywords=[...],
        )
```

#### ConfusionDetector (`confusion.py`)

Detects confusion markers in text:

```python
class ConfusionDetector:
    """
    Identifies linguistic markers of confusion:
    - Hedging words ("maybe", "I think", "not sure")
    - Questions embedded in answers
    - Contradictions
    - Vague pronouns ("it", "they" without clear referent)
    """
    
    CONFUSION_MARKERS = [
        "i don't understand",
        "confused",
        "what does",
        "i'm not sure",
        "maybe",
        "i think",
        ...
    ]
```

#### ReadabilityAnalyzer (`readability.py`)

Multiple readability indices:

```python
class ReadabilityAnalyzer:
    """
    Computes multiple readability scores:
    - Flesch Reading Ease (0-100, higher = easier)
    - Gunning Fog Index
    - SMOG Index
    - Coleman-Liau Index
    """
```

#### TopicDriftDetector (`topic_drift.py`)

Jaccard similarity for drift detection:

```python
class TopicDriftDetector:
    """
    Detects when student response drifts off-topic.
    
    Uses Jaccard similarity between response keywords
    and reference topic keywords.
    """
    
    def check(self, text: str, reference_keywords: list[str]) -> DriftResult:
        response_keywords = self._extract_keywords(text)
        similarity = self._jaccard_similarity(response_keywords, reference_keywords)
        return DriftResult(
            drift_detected=similarity < self._threshold,
            similarity_score=similarity,
        )
```

### 4.3 Integration with Collector

Added `record_text_event()` method to `AsyncEventCollector`:

```python
async def record_text_event(self, event: TextEvent) -> NLPResult:
    """Record text event and return NLP analysis."""
    nlp_result = self._nlp_pipeline.analyze(
        event.text,
        expected_keywords=event.expected_keywords,
    )
    event.nlp_result = nlp_result
    await self.record_event(event)
    return nlp_result
```

---

## Step 5: LangGraph Fusion Engine

**Commit:** `e13d783`  
**Tests Added:** 33 (Total: 245)  
**Description:** Multi-agent system for evaluating learning moments and generating interventions.

### 5.1 Eight Specialized Agents

**Directory:** `neurosync/fusion/agents/`

All agents inherit from `BaseAgent`:

```python
class BaseAgent(ABC):
    """Base class for all fusion agents."""
    
    @property
    @abstractmethod
    def moment_ids(self) -> list[str]:
        """Moment IDs this agent handles."""
        ...
    
    @abstractmethod
    async def evaluate(self, state: FusionState) -> list[InterventionProposal]:
        """Evaluate state and return intervention proposals."""
        ...
```

#### AttentionAgent (M01, M21)

```python
class AttentionAgent(BaseAgent):
    """
    Monitors attention drop and interruptions.
    
    Signals used:
    - Webcam: gaze direction, off-screen duration
    - Behavioral: idle time, tab visibility
    """
    
    @property
    def moment_ids(self) -> list[str]:
        return ["M01", "M21"]
        
    async def evaluate(self, state: FusionState) -> list[InterventionProposal]:
        if state.webcam and state.webcam.off_screen_duration_ms > 10000:
            return [InterventionProposal(
                moment_id="M01",
                urgency="next_pause",
                intervention_type="attention_recapture",
                ...
            )]
```

#### OverloadAgent (M02, M16)

```python
class OverloadAgent(BaseAgent):
    """
    Detects cognitive overload and working memory overflow.
    
    Signals used:
    - NLP: content complexity
    - Behavioral: rewind patterns, response times
    - Knowledge: chunk count, new concept rate
    """
```

#### GapAgent (M03)

```python
class GapAgent(BaseAgent):
    """
    Identifies knowledge gaps from prerequisite analysis.
    
    Signals used:
    - Knowledge: prerequisite mastery
    - NLP: answer quality, missing keywords
    - Behavioral: repeated wrong answers
    """
```

#### EngagementAgent (M06, M09)

```python
class EngagementAgent(BaseAgent):
    """
    Monitors boredom and confidence collapse.
    
    Signals used:
    - Webcam: boredom expression, gaze patterns
    - Behavioral: scroll speed, skip patterns
    - NLP: sentiment in responses
    """
```

#### FatigueAgent (M10, M11)

```python
class FatigueAgent(BaseAgent):
    """
    Tracks mental and physical fatigue.
    
    Signals used:
    - Webcam: blink rate, posture
    - Behavioral: response time degradation
    - Session: duration, time of day
    """
```

#### MemoryAgent (M17, M19)

```python
class MemoryAgent(BaseAgent):
    """
    Manages forgetting curve and sleep consolidation.
    
    Signals used:
    - Spaced repetition: predicted retention
    - Knowledge: time since last review
    - Session: time of day (for sleep window)
    """
```

#### MisconceptionAgent (M13, M15)

```python
class MisconceptionAgent(BaseAgent):
    """
    Detects wrong methods and misconceptions.
    
    Signals used:
    - Knowledge: misconception patterns
    - NLP: answer analysis
    - Behavioral: error patterns
    """
```

#### PlateauAgent (M22)

```python
class PlateauAgent(BaseAgent):
    """
    Identifies learning plateaus and suggests escape strategies.
    
    Signals used:
    - Knowledge: progress curve analysis
    - Behavioral: repeated attempts without improvement
    """
```

### 5.2 Fusion State

**File:** `neurosync/fusion/state.py`

Unified state passed to all agents:

```python
@dataclass
class FusionState:
    session_id: str
    student_id: str
    timestamp: float
    cycle_number: int
    
    behavioral: BehavioralSignals
    webcam: WebcamSignals | None
    knowledge: KnowledgeSignals
    nlp: NLPSignals | None
    
    session_duration_minutes: float
    lesson_position_ms: float
    recent_interventions: list[str]
    agent_states: dict[str, Any]
    
    proposed_interventions: list[InterventionProposal] = field(default_factory=list)

@dataclass
class InterventionProposal:
    moment_id: str
    urgency: Literal["immediate", "next_pause", "deferred"]
    intervention_type: str
    confidence: float
    context: dict[str, Any]
    suggested_content_params: dict[str, Any]
```

### 5.3 Fusion Graph

**File:** `neurosync/fusion/graph.py`

```python
class FusionGraph:
    """
    Executes all agents in parallel and collects proposals.
    """
    
    def __init__(self, agents: list[BaseAgent]):
        self._agents = agents
        
    async def execute(self, state: FusionState) -> FusionState:
        """Run all agents in parallel."""
        tasks = [agent.evaluate(state) for agent in self._agents]
        results = await asyncio.gather(*tasks)
        
        for proposals in results:
            state.proposed_interventions.extend(proposals)
            
        return state
```

### 5.4 Fusion Coordinator

**File:** `neurosync/fusion/coordinator.py`

Main fusion loop (called every 250 ms):

```python
class FusionCoordinator:
    """Entry-point for every 250 ms fusion cycle."""
    
    def __init__(self, agents: list[BaseAgent]):
        self.graph = FusionGraph(agents)
        self.prioritizer = InterventionPrioritizer()
        self.cooldown_tracker = CooldownTracker()
        self.conflict_resolver = ConflictResolver()
        
    async def process_cycle(
        self,
        session_id: str,
        student_id: str,
        behavioral: BehavioralSignals,
        webcam: WebcamSignals | None = None,
        knowledge: KnowledgeSignals | None = None,
        nlp: NLPSignals | None = None,
        ...
    ) -> list[InterventionProposal]:
        """
        Workflow:
        1. Build FusionState from all signal layers
        2. Execute graph (all 8 agents evaluate in parallel)
        3. Filter proposals by cooldowns
        4. Resolve conflicts between proposals
        5. Prioritize to max 2 non-conflicting interventions
        6. Return selected interventions to UI
        """
```

### 5.5 Decision Support

**Directory:** `neurosync/fusion/decision/`

#### CooldownTracker (`cooldown.py`)

Prevents intervention spamming:

```python
class CooldownTracker:
    """
    Enforces minimum time between same intervention types.
    
    Cooldowns:
    - attention_recapture: 60 seconds
    - simplify_content: 120 seconds
    - break_suggestion: 300 seconds
    """
    
    def filter_interventions(self, proposals: list[InterventionProposal], 
                            now: float) -> list[InterventionProposal]:
        return [p for p in proposals if not self._on_cooldown(p, now)]
```

#### ConflictResolver (`conflict_resolver.py`)

Resolves conflicting interventions:

```python
class ConflictResolver:
    """
    Resolves conflicts between intervention proposals.
    
    Conflict rules:
    - Can't simplify AND challenge simultaneously
    - Can't suggest break AND attention recapture
    - Prefer higher confidence proposal
    """
    
    CONFLICTS = {
        ("simplify", "challenge"): "simplify",
        ("break", "attention"): "break",
        ...
    }
```

#### InterventionPrioritizer (`prioritizer.py`)

Ranks and limits interventions:

```python
class InterventionPrioritizer:
    """
    Prioritizes interventions by urgency and confidence.
    
    Priority order:
    1. Immediate urgency
    2. Higher confidence
    3. More specific (single moment vs. multiple)
    """
    
    def prioritize(self, proposals: list[InterventionProposal], 
                   max_interventions: int = 2) -> list[InterventionProposal]:
        sorted_proposals = sorted(proposals, 
            key=lambda p: (self._urgency_score(p), p.confidence),
            reverse=True
        )
        return sorted_proposals[:max_interventions]
```

### 5.6 Top-Level Orchestrator

**File:** `neurosync/fusion/orchestrator.py`

```python
class NeuroSyncOrchestrator:
    """
    Highest-level coordinator. Call run_lesson_cycle() every 250 ms
    during active lesson playback.
    """
    
    def __init__(self, session_id: str, student_id: str):
        self.agents = [
            AttentionAgent(),
            OverloadAgent(),
            GapAgent(),
            EngagementAgent(),
            FatigueAgent(),
            MemoryAgent(),
            MisconceptionAgent(),
            PlateauAgent(),
        ]
        self.fusion = FusionCoordinator(self.agents)
        
    async def run_lesson_cycle(
        self,
        behavioral: BehavioralSignals,
        webcam: WebcamSignals | None,
    ) -> list[InterventionProposal]:
        return await self.fusion.process_cycle(...)
```

---

## Step 6: GPT-4 Intervention Engine

**Commit:** `6862e5e`  
**Tests Added:** 24 (Total: 167)  
**Description:** LLM-powered intervention content generation with caching and cost controls.

### 6.1 Six Prompt Builders

**Directory:** `neurosync/interventions/prompts/`

Each prompt builder creates structured prompts for GPT-4:

#### SimplifyPrompts (M02)

```python
class SimplifyPrompts:
    """
    Generates prompts to simplify complex content.
    
    Context needed:
    - Original content
    - Student grade level
    - Specific complexity issues
    """
    
    SYSTEM = """You are NeuroSync, an AI tutor. When simplifying, 
    maintain accuracy while reducing complexity. Use concrete examples."""
    
    def build(self, content: str, grade_level: int, 
              complexity_issues: list[str]) -> tuple[str, str]:
        return (self.SYSTEM, f"""
        Simplify this content for a grade {grade_level} student:
        
        Original: {content}
        
        Issues to address: {complexity_issues}
        
        Provide a simpler explanation that:
        1. Uses shorter sentences
        2. Replaces jargon with everyday words
        3. Includes a concrete analogy
        """)
```

#### ExplainPrompts (M03)

```python
class ExplainPrompts:
    """
    Generates prompts to explain concepts from scratch.
    
    For knowledge gaps - assumes zero prior knowledge.
    """
```

#### MisconceptionPrompts (M15)

```python
class MisconceptionPrompts:
    """
    Generates prompts to address misconceptions.
    
    Non-judgmental, empathetic approach.
    """
```

#### RescuePrompts (M07)

```python
class RescuePrompts:
    """
    Generates prompts to rescue from frustration.
    
    Validates difficulty, offers fresh perspective.
    """
```

#### PlateauPrompts (M22)

```python
class PlateauPrompts:
    """
    Generates prompts for new learning methods.
    
    Vivid, relatable analogies to break plateau.
    """
```

#### ApplicationPrompts (M18)

```python
class ApplicationPrompts:
    """
    Generates prompts for transfer/application questions.
    
    Questions require genuine understanding, not just recall.
    """
```

### 6.2 Intervention Generator

**File:** `neurosync/interventions/generator.py`

```python
class InterventionGenerator:
    """
    Generates intervention content using GPT-4.
    
    Features:
    - Async GPT-4 calls with retry logic
    - Rate limiting (requests per minute)
    - Two-tier caching (memory LRU + SQLite)
    - Cost tracking per session/student
    - Template fallbacks when API unavailable
    """
    
    async def generate(
        self,
        intervention_type: str,
        context: dict[str, Any],
    ) -> GeneratedContent:
        # 1. Check cache
        cache_key = self._compute_cache_key(intervention_type, context)
        cached = self._cache.get(cache_key)
        if cached:
            return cached
            
        # 2. Check cost limits
        if not self._cost_tracker.can_generate(self._session_id):
            return self._fallback_templates.get(intervention_type)
            
        # 3. Build prompt
        prompt_builder = _PROMPT_BUILDERS[intervention_type]
        system, user = prompt_builder.build(**context)
        
        # 4. Call GPT-4 with retry
        for attempt in range(self._max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                )
                break
            except Exception as e:
                if attempt == self._max_retries - 1:
                    return self._fallback_templates.get(intervention_type)
                await asyncio.sleep(2 ** attempt)
                
        # 5. Track cost and cache
        content = response.choices[0].message.content
        tokens = response.usage.total_tokens
        self._cost_tracker.record(self._session_id, tokens)
        self._cache.set(cache_key, content)
        
        return GeneratedContent(
            intervention_type=intervention_type,
            content=content,
            tokens_used=tokens,
            from_cache=False,
        )
```

### 6.3 Cache Manager

**File:** `neurosync/interventions/cache/manager.py`

Two-tier caching system:

```python
class CacheManager:
    """
    Two-tier cache: in-memory LRU + SQLite persistence.
    
    Cache key: hash(intervention_type + sorted(context))
    """
    
    def __init__(self, db: DatabaseManager, max_memory_items: int = 1000):
        self._memory_cache = LRUCache(maxsize=max_memory_items)
        self._db = db
        
    def get(self, key: str) -> str | None:
        # Check memory first
        if key in self._memory_cache:
            return self._memory_cache[key]
            
        # Check SQLite
        row = self._db.fetch_one(
            "SELECT content FROM intervention_cache WHERE cache_key = ?",
            (key,)
        )
        if row:
            self._memory_cache[key] = row["content"]
            return row["content"]
            
        return None
        
    def set(self, key: str, content: str) -> None:
        self._memory_cache[key] = content
        self._db.execute(
            "INSERT OR REPLACE INTO intervention_cache (cache_key, content, created_at) VALUES (?, ?, ?)",
            (key, content, time.time())
        )
```

### 6.4 Cost Tracker

**File:** `neurosync/interventions/cost_tracker.py`

```python
class CostTracker:
    """
    Tracks API usage and enforces cost limits.
    
    Limits (configurable):
    - Per session: 50,000 tokens
    - Per student per day: 200,000 tokens
    """
    
    def __init__(self, db: DatabaseManager):
        self._db = db
        self._session_limit = INTERVENTION_COST_LIMITS["SESSION_TOKEN_LIMIT"]
        self._daily_limit = INTERVENTION_COST_LIMITS["DAILY_TOKEN_LIMIT"]
        
    def can_generate(self, session_id: str) -> bool:
        session_usage = self._get_session_usage(session_id)
        return session_usage < self._session_limit
        
    def record(self, session_id: str, tokens: int) -> None:
        self._db.execute(
            "INSERT INTO token_usage (session_id, tokens, timestamp) VALUES (?, ?, ?)",
            (session_id, tokens, time.time())
        )
```

### 6.5 Fallback Templates

**File:** `neurosync/interventions/templates/fallbacks.py`

Pre-written templates when API unavailable:

```python
class FallbackTemplates:
    """
    Static fallback content when GPT-4 is unavailable.
    """
    
    TEMPLATES = {
        "simplify": """
        Let's break this down into simpler parts:
        
        The key idea is: {concept}
        
        Think of it like: {analogy}
        
        The main steps are:
        1. {step1}
        2. {step2}
        3. {step3}
        """,
        
        "rescue": """
        It's completely normal to find this challenging! 
        
        Let's try a different approach:
        {alternative_explanation}
        
        Take a moment, then we'll work through this together.
        """,
        ...
    }
```

### 6.6 Coordinator

**File:** `neurosync/interventions/coordinator.py`

Orchestrates request → content flow:

```python
class InterventionCoordinator:
    """
    Coordinates intervention request to generated content.
    """
    
    def __init__(self, generator: InterventionGenerator):
        self._generator = generator
        
    async def handle_request(
        self,
        request: InterventionRequest,
    ) -> InterventionResponse:
        content = await self._generator.generate(
            intervention_type=request.intervention_type,
            context=request.context,
        )
        
        return InterventionResponse(
            request_id=request.request_id,
            content=content,
            delivery_method=request.preferred_delivery,
        )
```

---

## Step 7: Content Generation Pipeline

**Commit:** `aacb9fb`  
**Tests Added:** 42 (Total: 212)  
**Description:** End-to-end content generation from PDF to video, slides, quiz, and story.

### 7.1 Pipeline Overview

**File:** `neurosync/content/pipeline.py`

```python
@dataclass
class PipelineConfig:
    # PDF Parsing
    max_pages: int = 200
    chunk_size: int = 4000
    
    # Concept Extraction
    extraction_model: str = "gpt-4-turbo-preview"
    
    # Generation
    max_slides_per_concept: int = 3
    tts_voice: str = "alloy"
    video_fps: int = 24
    
    # Feature flags
    generate_video: bool = True
    generate_slides: bool = True
    generate_notes: bool = True
    generate_story: bool = True
    generate_quiz: bool = True

class ContentPipeline:
    """
    End-to-end content generation workflow:
    
    PDF → Parse → Clean → Analyze → Extract Concepts →
    Generate (Slides + Scripts + Audio + Video + Story + Quiz) →
    Export all formats
    """
    
    async def process(self, pdf_path: str, config: PipelineConfig) -> PipelineResult:
        # 1. Parse PDF
        doc = self._parser.parse(pdf_path)
        
        # 2. Clean text
        cleaned = self._cleaner.clean(doc.text)
        
        # 3. Analyze structure and complexity
        structure = self._structure_analyzer.analyze(cleaned)
        complexity = self._complexity_assessor.assess(cleaned)
        
        # 4. Extract concepts (GPT-4)
        concept_map = await self._concept_extractor.extract(cleaned)
        
        # 5. Generate outputs in parallel
        tasks = []
        if config.generate_slides:
            tasks.append(self._slide_generator.generate(concept_map))
        if config.generate_notes:
            tasks.append(self._script_generator.generate(concept_map))
        if config.generate_story:
            tasks.append(self._story_generator.generate(concept_map))
        if config.generate_quiz:
            tasks.append(self._quiz_generator.generate(concept_map))
            
        results = await asyncio.gather(*tasks)
        
        # 6. Generate audio + video (sequential due to dependencies)
        if config.generate_audio:
            audio_files = await self._tts.synthesize(scripts)
        if config.generate_video:
            video = await self._video_assembler.assemble(slides, audio_files)
            
        return PipelineResult(...)
```

### 7.2 Parsers

**Directory:** `neurosync/content/parsers/`

#### PDFParser (`pdf_parser.py`)

```python
class PDFParser:
    """
    Extracts text and structure from PDF documents.
    
    Features:
    - Text extraction with layout preservation
    - Image extraction
    - Table detection
    - Heading hierarchy detection
    """
    
    def parse(self, pdf_path: str) -> PDFDocument:
        # Uses pypdf or pdfplumber
        ...
```

#### TextCleaner (`text_cleaner.py`)

```python
class TextCleaner:
    """
    Cleans and normalizes extracted text.
    
    Operations:
    - Remove headers/footers
    - Fix broken words (hy-phenation)
    - Normalize whitespace
    - Remove artifacts
    """
```

### 7.3 Analyzers

**Directory:** `neurosync/content/analyzers/`

#### ComplexityAssessor (`complexity_assessor.py`)

```python
class ComplexityAssessor:
    """
    Assesses content complexity for grade-appropriate adaptation.
    
    Output: ComplexityReport with grade level, vocabulary difficulty,
    concept density, and recommendations.
    """
```

#### ConceptExtractor (`concept_extractor.py`)

```python
class ConceptExtractor:
    """
    Uses GPT-4 to extract concept hierarchy from text.
    
    Output: ConceptMap with concepts, prerequisites, relationships.
    """
    
    async def extract(self, text: str) -> ConceptMap:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract concepts from:\n\n{text}"},
            ],
        )
        return self._parse_concept_map(response)
```

#### StructureAnalyzer (`structure_analyzer.py`)

```python
class StructureAnalyzer:
    """
    Analyzes document structure (headings, sections, flow).
    """
```

### 7.4 Generators

**Directory:** `neurosync/content/generators/`

#### SlideGenerator (`slide_generator.py`)

```python
class SlideGenerator:
    """
    Generates presentation slides from concept map.
    
    Output: SlideDeck with title slides, content slides, summary slides.
    """
    
    def generate(self, concept_map: ConceptMap) -> SlideDeck:
        slides = []
        
        # Title slide
        slides.append(Slide(type="title", title=concept_map.title))
        
        # Content slides (max 3 per concept)
        for concept in concept_map.concepts:
            concept_slides = self._generate_concept_slides(concept)
            slides.extend(concept_slides[:self._max_per_concept])
            
        # Summary slide
        slides.append(self._generate_summary_slide(concept_map))
        
        return SlideDeck(slides=slides)
```

#### ScriptGenerator (`script_generator.py`)

```python
class ScriptGenerator:
    """
    Generates narration scripts for each slide.
    
    Uses GPT-4 to create conversational, educational narration.
    """
    
    async def generate(self, slide_deck: SlideDeck) -> FullScript:
        scripts = []
        for slide in slide_deck.slides:
            script = await self._generate_slide_script(slide)
            scripts.append(script)
        return FullScript(scripts=scripts)
```

#### StoryGenerator (`story_generator.py`)

```python
class StoryGenerator:
    """
    Generates narrative story explanations.
    
    Creates engaging stories that teach concepts through narrative.
    """
    
    async def generate(self, concept_map: ConceptMap) -> FullStory:
        # Generate story with characters, plot that illustrates concepts
        ...
```

#### QuizGenerator (`quiz_generator.py`)

```python
class QuizGenerator:
    """
    Generates assessment questions for each concept.
    
    Question types:
    - Multiple choice
    - Fill in the blank
    - Short answer
    - Application problems
    """
    
    async def generate(self, concept_map: ConceptMap) -> QuizBank:
        quiz_bank = QuizBank()
        
        for concept in concept_map.concepts:
            questions = await self._generate_concept_questions(concept)
            quiz_bank.add_questions(concept.id, questions)
            
        return quiz_bank
```

#### VideoAssembler (`video_assembler.py`)

```python
class VideoAssembler:
    """
    Assembles video from slides and audio.
    
    Uses moviepy for video generation.
    """
    
    async def assemble(
        self,
        slides: SlideDeck,
        audio_files: list[Path],
    ) -> Path:
        clips = []
        
        for slide, audio in zip(slides.slides, audio_files):
            # Create image clip from slide
            image_clip = ImageClip(slide.render())
            
            # Set duration from audio
            audio_clip = AudioFileClip(str(audio))
            image_clip = image_clip.set_duration(audio_clip.duration)
            image_clip = image_clip.set_audio(audio_clip)
            
            clips.append(image_clip)
            
        final = concatenate_videoclips(clips)
        output_path = self._output_dir / "lesson.mp4"
        final.write_videofile(str(output_path), fps=self._fps)
        
        return output_path
```

### 7.5 TTS Integration

**File:** `neurosync/content/tts/openai_tts.py`

```python
class OpenAITTS:
    """
    Text-to-speech using OpenAI's TTS API.
    """
    
    async def synthesize(self, scripts: list[str]) -> list[Path]:
        audio_files = []
        
        for i, script in enumerate(scripts):
            response = await self._client.audio.speech.create(
                model=self._model,  # "tts-1" or "tts-1-hd"
                voice=self._voice,  # alloy, echo, fable, onyx, nova, shimmer
                input=script,
            )
            
            audio_path = self._output_dir / f"audio_{i:03d}.mp3"
            with open(audio_path, "wb") as f:
                f.write(response.content)
                
            audio_files.append(audio_path)
            
        return audio_files
```

### 7.6 Export Formats

**Directory:** `neurosync/content/formats/`

- `MarkdownGenerator` — Export notes as Markdown
- `QuizExporter` — Export quizzes (JSON, Markdown, CSV)
- `StoryExporter` — Export stories (Markdown, HTML)

---

## Step 8: Spaced Repetition Engine

**Commit:** `2df1b31`  
**Tests Added:** 22 (Total: 267)  
**Description:** Personalized forgetting curve modeling and adaptive review scheduling.

### 8.1 Forgetting Curve Models

**File:** `neurosync/spaced_repetition/forgetting_curve/models.py`

```python
@dataclass
class RetentionPoint:
    """A single measurement of retention."""
    time_hours: float          # Hours since initial learning
    score: float               # 0.0 - 1.0 retention score
    timestamp: float           # Unix timestamp

@dataclass
class FittedCurve:
    """Result of fitting a forgetting curve."""
    tau_days: float            # Time constant (days until 37% retention)
    r0: float                  # Initial retention (usually ~0.95)
    model: str                 # "exponential" or "default"
    confidence: float          # R² goodness of fit
    data_points: int
    fitted_params: dict

@dataclass
class ReviewSchedule:
    """Scheduled review for a concept."""
    concept_id: str
    scheduled_at: float
    review_number: int
    predicted_retention: float
```

### 8.2 Forgetting Curve Fitter

**File:** `neurosync/spaced_repetition/forgetting_curve/fitter.py`

```python
class ForgettingCurveFitter:
    """
    Fits R(t) = R₀ · exp(−t/τ) to retention data using scipy.
    
    The exponential decay model:
    - R(t): Retention at time t
    - R₀: Initial retention (~0.95)
    - τ: Time constant (characteristic forgetting rate)
    """
    
    def fit_curve(self, retention_data: list[RetentionPoint]) -> FittedCurve:
        if len(retention_data) < self.min_data_points:
            # Return default curve for new students
            return FittedCurve(tau_days=self.default_tau, r0=0.95, model="default")
            
        # Convert to numpy arrays
        times_days = np.array([p.time_hours / 24.0 for p in retention_data])
        retention = np.array([p.score for p in retention_data])
        
        # Fit using scipy.optimize.curve_fit
        params, _ = curve_fit(
            lambda t, r0, tau: r0 * np.exp(-t / tau),
            times_days,
            retention,
            p0=[0.95, self.default_tau],
            bounds=([0.5, 0.5], [1.0, 60.0]),
        )
        
        r0_fitted, tau_fitted = params
        
        # Compute R² goodness of fit
        predictions = r0_fitted * np.exp(-times_days / tau_fitted)
        r_squared = 1 - np.sum((retention - predictions)**2) / np.sum((retention - np.mean(retention))**2)
        
        return FittedCurve(
            tau_days=tau_fitted,
            r0=r0_fitted,
            model="exponential",
            confidence=r_squared,
        )
```

### 8.3 Retention Predictor

**File:** `neurosync/spaced_repetition/forgetting_curve/predictor.py`

```python
class RetentionPredictor:
    """
    Predicts retention at future time points.
    """
    
    def predict(self, curve: FittedCurve, hours_since_learning: float) -> float:
        """Predict retention at given time."""
        days = hours_since_learning / 24.0
        return curve.r0 * math.exp(-days / curve.tau_days)
        
    def optimal_review_time(self, curve: FittedCurve, 
                           target_retention: float = 0.85) -> float:
        """
        Calculate optimal review time to maintain target retention.
        
        Solving: target = R₀ · exp(−t/τ) for t
        t = −τ · ln(target/R₀)
        """
        days = -curve.tau_days * math.log(target_retention / curve.r0)
        return days * 24.0  # Return hours
```

### 8.4 Main Scheduler

**File:** `neurosync/spaced_repetition/scheduler.py`

```python
class SpacedRepetitionScheduler:
    """
    Central coordinator for spaced repetition.
    
    Schedule expansion pattern:
    - Review 1: 1 day after mastery
    - Review 2: 3 days after review 1
    - Review 3: 7 days after review 2
    - Review 4: 14 days after review 3
    - Review 5+: 30 days (or based on fitted curve)
    """
    
    def record_mastery(
        self,
        student_id: str,
        concept_id: str,
        initial_score: float,
    ) -> None:
        """Record initial mastery and schedule first review."""
        # Store mastery record
        # Schedule first review at optimal time
        first_review = self._predictor.optimal_review_time(
            self._fitter.default_curve(),
            target_retention=0.85,
        )
        self._schedule_review(student_id, concept_id, first_review)
        
    def record_review(
        self,
        student_id: str,
        concept_id: str,
        score: float,
    ) -> None:
        """Record review result, refit curve, schedule next review."""
        # Add data point to retention history
        self._add_retention_point(student_id, concept_id, score)
        
        # Refit personalized curve
        history = self._get_retention_history(student_id, concept_id)
        curve = self._fitter.fit_curve(history)
        
        # Schedule next review
        next_review = self._predictor.optimal_review_time(curve)
        self._schedule_review(student_id, concept_id, next_review)
        
    def get_due_reviews(self, student_id: str) -> list[DueReview]:
        """Get all reviews due now or overdue."""
        now = time.time()
        due = self._db.fetch_all(
            "SELECT * FROM mastery_records WHERE student_id = ? AND next_review_at <= ?",
            (student_id, now)
        )
        return [self._to_due_review(row) for row in due]
```

### 8.5 Review Quiz Generator

**File:** `neurosync/spaced_repetition/quiz/generator.py`

```python
class ReviewQuizGenerator:
    """
    Generates quizzes for spaced repetition reviews.
    
    Features:
    - Varies question types across reviews
    - Increases difficulty on successive reviews
    - Includes application questions on later reviews
    """
    
    def generate(self, concept_id: str, review_number: int) -> ReviewQuiz:
        if review_number <= 2:
            # Early reviews: recognition and recall
            return self._generate_basic_quiz(concept_id)
        else:
            # Later reviews: application and transfer
            return self._generate_advanced_quiz(concept_id)
```

### 8.6 Timing Optimization

**Directory:** `neurosync/spaced_repetition/timing/`

- Circadian-aware scheduling (prefer morning reviews)
- Sleep window integration (M19 - don't schedule during optimal sleep)
- Workload distribution (avoid review bunching)

### 8.7 Analytics

**File:** `neurosync/spaced_repetition/analytics.py`

```python
class SpacedRepetitionAnalytics:
    """
    Analytics for spaced repetition effectiveness.
    
    Metrics:
    - Average retention at review time
    - Curve fit accuracy over time
    - Review completion rate
    - Long-term retention trends
    """
```

---

## Step 9: Pre-Lesson Readiness Protocol

**Commit:** `8bfc024`  
**Tests Added:** 18 (Total: 285)  
**Description:** Pre-lesson anxiety detection and calming interventions.

### 9.1 Three Assessments

**Directory:** `neurosync/readiness/assessments/`

#### Self-Report Assessment (`self_report.py`)

```python
class SelfReportResult:
    anxiety_score: float       # 0.0 - 1.0
    mood_score: float
    energy_level: float
    responses: dict[str, int]

def score_responses(responses: dict[str, int]) -> SelfReportResult:
    """
    Score self-report questionnaire.
    
    Questions:
    - "How are you feeling right now?" (1-5)
    - "How confident do you feel about this topic?" (1-5)
    - "How focused can you be right now?" (1-5)
    - "How anxious do you feel?" (1-5, reverse scored)
    """
    ...
```

#### Physiological Assessment (`physiological.py`)

```python
class PhysiologicalResult:
    available: bool            # Whether webcam data is available
    blink_rate: float
    anxiety_score: float       # Derived from blink rate
    confidence: float

def assess_blink_rate(blink_rate: float | None) -> PhysiologicalResult:
    """
    Assess anxiety from blink rate.
    
    Elevated blink rate (>25/min) indicates anxiety.
    Very high (>35/min) indicates high stress.
    """
    if blink_rate is None:
        return PhysiologicalResult(available=False, anxiety_score=0.0)
        
    anxiety = 0.0
    if blink_rate > 35:
        anxiety = 0.8
    elif blink_rate > 25:
        anxiety = 0.5
    elif blink_rate > 20:
        anxiety = 0.3
        
    return PhysiologicalResult(
        available=True,
        blink_rate=blink_rate,
        anxiety_score=anxiety,
    )
```

#### Behavioral Assessment (`behavioral.py`)

```python
class BehavioralResult:
    response_time_ms: float
    accuracy: float
    anxiety_score: float

def assess_warmup(warmup_answers: list[WarmupAnswer]) -> BehavioralResult:
    """
    Assess anxiety from warmup task performance.
    
    Warmup: 3-5 simple questions to gauge current state.
    
    High anxiety indicators:
    - Slower than usual response times
    - Lower than usual accuracy
    - High response time variance
    """
    ...
```

### 9.2 Readiness Checker

**File:** `neurosync/readiness/checker.py`

```python
def run_check(
    session_id: str,
    student_id: str,
    lesson_topic: str,
    self_report_responses: dict[str, int] | None = None,
    blink_rate: float | None = None,
    warmup_answers: list[WarmupAnswer] | None = None,
) -> ReadinessCheckResult:
    """
    Execute full readiness check.
    
    Workflow:
    1. Run self-report assessment
    2. Run physiological (blink-rate) assessment
    3. Run behavioral warmup assessment
    4. Compute combined readiness score
    5. If anxiety high → offer breathing exercise → optional recheck
    6. Persist result
    """
    # 1. Self-report
    sr = score_responses(self_report_responses or {})
    
    # 2. Physiological
    phys = assess_blink_rate(blink_rate)
    
    # 3. Behavioral
    behav = assess_warmup(warmup_answers or [])
    
    # 4. Combined score
    combined = compute_readiness_score(sr, phys, behav)
    
    # 5. Determine status
    if combined.readiness_score >= READY_THRESHOLD:
        status = "ready"
    elif combined.anxiety_score > ANXIETY_THRESHOLD:
        status = "needs_intervention"
    else:
        status = "not_ready"
        
    return ReadinessCheckResult(
        session_id=session_id,
        student_id=student_id,
        readiness_score=combined.readiness_score,
        anxiety_score=combined.anxiety_score,
        status=status,
        ...
    )
```

### 9.3 Readiness Scorer

**File:** `neurosync/readiness/scorer.py`

```python
def compute(
    self_report_anxiety: float,
    physiological_anxiety: float,
    behavioral_anxiety: float,
    webcam_available: bool,
) -> CombinedScore:
    """
    Weighted combination of anxiety signals.
    
    Weights (with webcam):
    - Self-report: 0.35
    - Physiological: 0.35
    - Behavioral: 0.30
    
    Weights (without webcam):
    - Self-report: 0.50
    - Behavioral: 0.50
    """
    if webcam_available:
        anxiety = (
            self_report_anxiety * 0.35 +
            physiological_anxiety * 0.35 +
            behavioral_anxiety * 0.30
        )
    else:
        anxiety = (
            self_report_anxiety * 0.50 +
            behavioral_anxiety * 0.50
        )
        
    readiness = 1.0 - anxiety
    
    return CombinedScore(readiness_score=readiness, anxiety_score=anxiety)
```

### 9.4 Breathing Exercise Intervention

**File:** `neurosync/readiness/interventions/breathing.py`

```python
# 4-4-6 breathing pattern
INHALE: float = 4.0   # seconds
HOLD: float = 4.0     # seconds
EXHALE: float = 6.0   # seconds
CYCLES: int = 8       # repetitions

# Total duration: (4 + 4 + 6) × 8 = 112 seconds

class BreathPhase(Enum):
    INHALE = "inhale"
    HOLD = "hold"
    EXHALE = "exhale"
    COMPLETE = "complete"

@dataclass
class BreathState:
    elapsed_seconds: float
    current_cycle: int
    phase: BreathPhase
    phase_progress: float  # 0.0 - 1.0
    is_complete: bool

def phase_at(elapsed: float) -> BreathState:
    """
    Return breathing state at given elapsed time.
    
    Used by UI to display real-time guidance animation.
    """
    if elapsed >= TOTAL_DURATION:
        return BreathState(phase=BreathPhase.COMPLETE, is_complete=True)
        
    cycle_index = int(elapsed // CYCLE_DURATION)
    within_cycle = elapsed - cycle_index * CYCLE_DURATION
    
    if within_cycle < INHALE:
        phase = BreathPhase.INHALE
        progress = within_cycle / INHALE
    elif within_cycle < INHALE + HOLD:
        phase = BreathPhase.HOLD
        progress = (within_cycle - INHALE) / HOLD
    else:
        phase = BreathPhase.EXHALE
        progress = (within_cycle - INHALE - HOLD) / EXHALE
        
    return BreathState(
        elapsed_seconds=elapsed,
        current_cycle=cycle_index + 1,
        phase=phase,
        phase_progress=progress,
    )
```

### 9.5 Other Interventions

**Directory:** `neurosync/readiness/interventions/`

#### DifficultyAdjuster (`difficulty_adjuster.py`)

```python
class DifficultyAdjuster:
    """
    Adjusts lesson difficulty based on readiness state.
    
    Low readiness → Start with easier content
    High anxiety → Reduce cognitive load
    """
```

#### PrerequisiteReview (`prerequisite_review.py`)

```python
class PrerequisiteReviewer:
    """
    Suggests prerequisite review if warmup reveals gaps.
    """
```

### 9.6 UI Components

**File:** `neurosync/readiness/ui_components.py`

```python
@dataclass
class BreathingUIState:
    """State for breathing exercise UI."""
    circle_scale: float        # For animation
    instruction_text: str      # "Breathe in...", "Hold...", "Breathe out..."
    progress_percent: float
    cycle_display: str         # "Cycle 3 of 8"

@dataclass
class CheckpointUIState:
    """State for readiness checkpoint UI."""
    current_step: int
    total_steps: int
    step_label: str
    can_continue: bool
```

---

## Step 10: EEG Integration (Planned)

**Status:** Not yet implemented  
**Description:** Integration with consumer EEG headsets for direct neural signal monitoring.

### Planned Features:

#### Signal Types
- **Theta waves (4-8 Hz):** Mental effort, confusion
- **Alpha waves (8-12 Hz):** Relaxation, disengagement
- **Beta waves (12-30 Hz):** Active thinking, focus
- **Gamma waves (30-100 Hz):** Higher cognitive processing

#### Planned Detectors
- `WorkingMemoryLoadDetector` — Theta/alpha ratio
- `EngagementDetector` — Beta power
- `FatigueDetector` — Alpha increase over time
- `InsightDetector` — Gamma bursts

#### Integration Points
Current placeholders in code:

```python
# In FrustrationDetector.detect()
eeg_theta_high: float = 0.0  # Placeholder for Step 10

# In SessionConfig
eeg_enabled: bool = False    # Flag for EEG-enabled sessions
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          NeuroSyncOrchestrator                          │
│                         (main loop every 250ms)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   SIGNAL LAYERS (Steps 1-4)                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│   │ Behavioral  │  │   Webcam    │  │  Knowledge  │  │     NLP     │  │
│   │  Collector  │  │   Fusion    │  │    Graph    │  │  Pipeline   │  │
│   │  (Step 1)   │  │  (Step 2)   │  │  (Step 3)   │  │  (Step 4)   │  │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│          │                │                │                │          │
│          └────────────────┴────────────────┴────────────────┘          │
│                                   │                                     │
│                                   ▼                                     │
│   FUSION LAYER (Step 5)                                                 │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    LangGraph Fusion Engine                       │  │
│   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │  │
│   │  │ Attention │ │ Overload  │ │    Gap    │ │Engagement │       │  │
│   │  │   Agent   │ │   Agent   │ │   Agent   │ │   Agent   │       │  │
│   │  └───────────┘ └───────────┘ └───────────┘ └───────────┘       │  │
│   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │  │
│   │  │  Fatigue  │ │  Memory   │ │Misconception│ │ Plateau  │       │  │
│   │  │   Agent   │ │   Agent   │ │   Agent   │ │   Agent   │       │  │
│   │  └───────────┘ └───────────┘ └───────────┘ └───────────┘       │  │
│   │                                                                  │  │
│   │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │  │
│   │  │   Cooldown    │ │   Conflict    │ │  Prioritizer  │         │  │
│   │  │   Tracker     │ │   Resolver    │ │               │         │  │
│   │  └───────────────┘ └───────────────┘ └───────────────┘         │  │
│   └──────────────────────────────┬──────────────────────────────────┘  │
│                                  │                                      │
│                                  ▼                                      │
│   INTERVENTION LAYER (Step 6)                                           │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                  GPT-4 Intervention Engine                       │  │
│   │  ┌─────────────────────────────────────────┐ ┌───────────────┐  │  │
│   │  │            Prompt Builders              │ │     Cache     │  │  │
│   │  │  Simplify │ Explain │ Misconception    │ │   + Cost      │  │  │
│   │  │  Rescue   │ Plateau │ Application      │ │   Tracker     │  │  │
│   │  └─────────────────────────────────────────┘ └───────────────┘  │  │
│   └──────────────────────────────┬──────────────────────────────────┘  │
│                                  │                                      │
│                                  ▼                                      │
│                           [ UI / Frontend ]                             │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   SUPPORTING SYSTEMS                                                    │
│                                                                         │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│   │     Content     │  │     Spaced      │  │    Readiness    │        │
│   │    Pipeline     │  │   Repetition    │  │    Protocol     │        │
│   │    (Step 7)     │  │    (Step 8)     │  │    (Step 9)     │        │
│   │                 │  │                 │  │                 │        │
│   │ PDF → Parse →   │  │ Forgetting →    │  │ Self-Report →   │        │
│   │ Analyze →       │  │ Curve Fit →     │  │ Physiological → │        │
│   │ Slides/Video/   │  │ Schedule →      │  │ Behavioral →    │        │
│   │ Quiz/Story      │  │ Review Quiz     │  │ Breathing       │        │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

                           ┌─────────────────┐
                           │    Database     │
                           │    (SQLite)     │
                           │                 │
                           │ • Sessions      │
                           │ • Events        │
                           │ • Signals       │
                           │ • Mastery       │
                           │ • Interventions │
                           │ • Cache         │
                           │ • Readiness     │
                           └─────────────────┘
```

---

## Test Coverage Summary

### Test Files by Module

| Module | Test File | Tests |
|--------|-----------|-------|
| Behavioral | test_behavioral.py, test_collector.py, test_signals.py, test_moments.py | 41 |
| Webcam | test_webcam_*.py (5 files) | 20 |
| Knowledge | test_graph_*.py (7 files) | 43 |
| NLP | test_nlp_*.py (5 files) | 39 |
| Fusion | test_agents.py, test_orchestrator.py, test_coordinator.py, test_conflict_resolver.py, test_cooldown.py, test_prioritizer.py | 33 |
| Interventions | test_generator.py, test_cache.py, test_cost_tracker.py, test_*_prompts.py (6 files) | 24 |
| Content | test_pipeline.py, test_*_generator.py (5 files), test_pdf_parser.py, test_concept_extractor.py | 42 |
| Spaced Rep | test_forgetting_curve.py, test_spaced_scheduler.py, test_sr_*.py | 22 |
| Readiness | test_checker.py, test_scorer.py, test_breathing.py, test_self_report.py, test_physiological.py | 18 |

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=neurosync --cov-report=html

# Run specific module
pytest tests/test_behavioral.py

# Run with verbose output
pytest -v
```

---

## Dependencies

### Core Requirements (requirements.txt)

```
# Core
pydantic>=2.0.0
loguru>=0.7.0
numpy>=1.24.0
scipy>=1.10.0

# Database
# sqlite3 (built-in)

# NLP
textblob>=0.18.0
textstat>=0.7.3

# Computer Vision
opencv-python>=4.8.0
mediapipe>=0.10.0

# Knowledge Graph
neo4j>=5.0.0

# LLM
openai>=1.0.0

# Content Generation
pypdf>=3.0.0
moviepy>=1.0.3

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
```

### Optional Dependencies

```
# For video generation
pillow>=10.0.0
imageio>=2.31.0

# For audio
pydub>=0.25.0

# For advanced NLP
spacy>=3.6.0
transformers>=4.30.0
```

---

## File Structure Summary

```
neurosync/
├── __init__.py
├── behavioral/           # Step 1: Behavioral signals
│   ├── collector.py
│   ├── fusion.py
│   ├── moments.py
│   └── signals.py
├── config/
│   └── settings.py
├── content/              # Step 7: Content generation
│   ├── analyzers/
│   ├── formats/
│   ├── generators/
│   ├── parsers/
│   ├── pipeline.py
│   └── tts/
├── core/
│   ├── constants.py
│   └── events.py
├── database/
│   ├── manager.py
│   ├── repositories/
│   └── schema.sql
├── fusion/               # Step 5: LangGraph fusion
│   ├── agents/
│   ├── coordinator.py
│   ├── decision/
│   ├── graph.py
│   ├── orchestrator.py
│   └── state.py
├── interventions/        # Step 6: GPT-4 interventions
│   ├── cache/
│   ├── coordinator.py
│   ├── cost_tracker.py
│   ├── generator.py
│   ├── prompts/
│   └── templates/
├── knowledge/            # Step 3: Neo4j knowledge graph
│   ├── detectors/
│   ├── graph_manager.py
│   ├── repositories/
│   ├── schema.cypher
│   └── seeders/
├── nlp/                  # Step 4: NLP pipeline
│   ├── pipeline.py
│   └── processors/
├── readiness/            # Step 9: Pre-lesson readiness
│   ├── assessments/
│   ├── checker.py
│   ├── interventions/
│   ├── scorer.py
│   └── ui_components.py
├── spaced_repetition/    # Step 8: Spaced repetition
│   ├── analytics.py
│   ├── forgetting_curve/
│   ├── notifications/
│   ├── quiz/
│   ├── scheduler.py
│   └── timing/
└── webcam/               # Step 2: Webcam signals
    ├── capture.py
    ├── fusion.py
    ├── injector.py
    ├── mediapipe_processor.py
    └── signals/
```

---

## Conclusion

NeuroSync-AI implements a comprehensive adaptive learning system across 9 completed steps (285 tests passing). The architecture is designed for:

1. **Real-time detection** of 22 learning failure moments
2. **Multi-modal signal fusion** from behavioral, visual, linguistic, and knowledge sources
3. **Personalized interventions** powered by GPT-4 with caching and cost controls
4. **Long-term retention** through personalized forgetting curves
5. **Student wellbeing** through pre-lesson readiness assessment

Step 10 (EEG integration) remains as future work, with placeholders already in place throughout the codebase.
