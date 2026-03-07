# NeuroSync AI v5.1 -- System Architecture

## 1. Overview

NeuroSync AI is an intelligent tutoring platform that detects 22 distinct
learning failure moments in real time and generates targeted interventions
to keep students on track.  The system fuses behavioral telemetry, optional
webcam signals (MediaPipe), optional NLP analysis, and optional EEG data
through 8 parallel LangGraph-style agents running on a 250 ms cycle.
Course content is generated from uploaded PDFs through an 11-stage async
pipeline using Groq LLM and gTTS at $0 operational cost.

Key properties:

- **22 failure moments** (M01--M22): attention drop, cognitive overload,
  knowledge gap, misconception, fatigue, frustration, and 16 more.
- **$0 cost architecture**: Groq (free tier) for LLM, gTTS (free) for
  text-to-speech, Neo4j Community for graph storage.
- **Graceful degradation**: every optional signal source (webcam, NLP, EEG)
  can be absent; the system continues with whatever is available.
- **Tiered confidence**: primary detection uses always-available signals;
  EEG adds up to +0.20 confidence when hardware is present and quality >= 0.6.

---

## 2. High-Level Architecture

```
+=========================================================================+
|                        PRESENTATION LAYER                               |
|   React 18 + TypeScript + Tailwind CSS + Electron 28 + Vite 5          |
|   (Zustand state, React Query, D3 knowledge map, Recharts analytics)   |
+=========================================================================+
        |  HTTP / WebSocket (localhost:8000)            |  Electron IPC
        v                                              v
+=========================================================================+
|                        APPLICATION LAYER                                |
|   FastAPI v5.1 + WebSocket (250 ms push)                               |
|   Routes: /session, /signals, /interventions, /content, /ws/{id}       |
|   Schemas: Pydantic v2 request/response models                         |
+=========================================================================+
        |                     |                     |
        v                     v                     v
+=====================+  +============================+  +================+
|   DETECTION LAYER   |  |   CONTENT GENERATION LAYER |  |   DATA LAYER   |
|                     |  |                            |  |                |
| 22 Moment Detectors |  |  11-stage async pipeline   |  | Neo4j (graph)  |
| (BaseMomentDetector)|  |  PDF -> Course materials   |  | SQLite (events)|
|                     |  |                            |  | File system    |
| Fusion Orchestrator |  |  Groq LLM + gTTS          |  | (audio/video)  |
| 8 LangGraph agents  |  |  Video Assembler           |  |                |
| asyncio.gather()    |  |  Quiz + Story generators   |  |                |
+=====================+  +============================+  +================+
        ^                          ^
        |                          |
+=========================================================================+
|                     SIGNAL COLLECTION LAYER                             |
|                                                                         |
|  Behavioral (always)  |  Webcam/MediaPipe  |  NLP Pipeline  |  EEG     |
|  - Response times     |  (optional)        |  (optional)    | (optional)|
|  - Rewind patterns    |  - Gaze tracking   |  - Sentiment   | - Alpha  |
|  - Idle detection     |  - Blink rate      |  - Complexity  | - Beta   |
|  - Answer accuracy    |  - Expression      |  - Confusion   | - Theta  |
|  - Interaction var.   |  - Pose/fidget     |  - Keywords    | - Gamma  |
+=========================================================================+
```

### Layer Summary

| Layer                  | Technology                              | Always Required |
|------------------------|-----------------------------------------|-----------------|
| Presentation           | React 18, TypeScript, Electron 28       | Yes             |
| Application            | FastAPI, WebSocket, Pydantic v2         | Yes             |
| Detection              | LangGraph-style graph, asyncio          | Yes             |
| Signal Collection      | Behavioral collector, MediaPipe, spaCy  | Behavioral only |
| Content Generation     | Groq LLM, gTTS, pdfplumber, Pillow     | For content     |
| Data                   | Neo4j, SQLite, file system              | SQLite minimum  |

---

## 3. Component Details

### 3.1 Content Pipeline

**Module**: `neurosync/content/pipeline.py` -- class `ContentPipeline`

An 11-stage async pipeline that converts a PDF into 5 output formats at $0
cost (Groq free tier + gTTS).

```
PDF File
  |
  v
+------------------+     +------------------+     +---------------------+
| Stage 1: Parse   | --> | Stage 2: Clean   | --> | Stage 3: Analyze    |
| PDFParser         |     | TextCleaner      |     | StructureAnalyzer   |
| (pdfplumber)      |     | (regex, unicode) |     | ComplexityAssessor  |
+------------------+     +------------------+     +---------------------+
  |
  v
+---------------------------+
| Stage 4: Extract Concepts |
| ConceptExtractor          |
| (Groq llama-3.3-70b)     |
+---------------------------+
  |
  +-------+-------+-------+-------+-------+
  |       |       |       |       |       |
  v       v       v       v       v       v
 S5      S6      S7      S8      S9      S10      S11
Slides  Scripts  Audio   Video   Story   Quiz    Export
 .pptx  (LLM)   (gTTS)  (.mp4)  (.md)  (.json)  (notes)
```

| Stage | Class / Module              | Description                                  |
|-------|-----------------------------|----------------------------------------------|
| 1     | `PDFParser`                 | Extract text + tables via pdfplumber          |
| 2     | `TextCleaner`               | Normalize unicode, strip artifacts, title     |
| 3     | `StructureAnalyzer` + `ComplexityAssessor` | Heading hierarchy, Flesch-Kincaid  |
| 4     | `ConceptExtractor`          | Groq LLM (llama-3.3-70b) chunked extraction  |
| 5     | `SlideGenerator`            | PPTX slide deck from concepts                 |
| 6     | `ScriptGenerator`           | Narration scripts via Groq LLM               |
| 7     | gTTS / OpenAI TTS           | Text-to-speech audio per slide                |
| 8     | `VideoAssembler`            | Combine slides + audio into MP4 (Pillow+ffmpeg)|
| 9     | `StoryGenerator`            | Narrative story format via Groq LLM          |
| 10    | `QuizGenerator`             | Multi-choice questions via Groq LLM          |
| 11    | `MarkdownGenerator`         | Study notes export                            |

**Configuration**: `PipelineConfig` dataclass -- model `llama-3.3-70b-versatile`,
chunk size 4000 chars with 200-char overlap, max 200 pages, 1920x1080 video
at 24 fps.

---

### 3.2 Fusion Engine

**Module**: `neurosync/fusion/` -- classes `FusionCoordinator`, `FusionGraph`

The fusion engine runs on a 250 ms cycle.  Each cycle:

```
                     +------------------+
                     | FusionCoordinator|
                     | (entry point)    |
                     +--------+---------+
                              |
                    1. Build FusionState
                              |
                              v
                     +------------------+
                     |   FusionGraph    |
                     | asyncio.gather() |
                     +--------+---------+
                              |
          +---+---+---+---+---+---+---+---+
          |   |   |   |   |   |   |   |   |
          v   v   v   v   v   v   v   v   v
        [A1] [A2] [A3] [A4] [A5] [A6] [A7] [A8]
         |    |    |    |    |    |    |    |
         +----+----+----+----+----+----+----+
                              |
                    2. Collect AgentEvaluations
                              |
                              v
                     +------------------+
                     | CooldownTracker  |  3. Filter by cooldowns
                     +--------+---------+
                              |
                              v
                     +------------------+
                     | ConflictResolver |  4. Remove conflicting
                     +--------+---------+
                              |
                              v
                     +------------------+
                     | Prioritizer      |  5. Select top 2
                     +--------+---------+
                              |
                              v
                    InterventionProposal[]
                    (sent to UI via WS)
```

**8 Agents** (all inherit `BaseAgent`, implement `evaluate(FusionState) -> AgentEvaluation`):

| Agent               | Module                      | Monitored Moments       |
|----------------------|-----------------------------|------------------------|
| AttentionAgent       | `agents/attention_agent.py` | M01 (attention drop)   |
| OverloadAgent        | `agents/overload_agent.py`  | M02 (cognitive load)   |
| GapAgent             | `agents/gap_agent.py`       | M03 (knowledge gap)    |
| EngagementAgent      | `agents/engagement_agent.py`| M06 (boredom), M08     |
| FatigueAgent         | `agents/fatigue_agent.py`   | M10 (fatigue)          |
| MemoryAgent          | `agents/memory_agent.py`    | M16 (WM overflow)      |
| MisconceptionAgent   | `agents/misconception_agent.py` | M15 (misconception)|
| PlateauAgent         | `agents/plateau_agent.py`   | M22 (plateau escape)   |

**Shared State**: `FusionState` (Pydantic v2 model) contains:
- `BehavioralSignals` -- frustration, fatigue, response times, rewinds, idle
- `WebcamSignals` (optional) -- attention, off-screen, expression, blink
- `KnowledgeSignals` -- mastery, gaps, misconceptions, plateau
- `NLPSignals` (optional) -- complexity, confusion, sentiment, entities
- `EEGSignals` (optional) -- alpha/beta/theta/gamma power, quality gate

**Decision Pipeline**:
- `CooldownTracker` -- prevents re-firing the same intervention within N seconds
- `ConflictResolver` -- removes incompatible simultaneous interventions
- `InterventionPrioritizer` -- selects max 2 non-conflicting proposals per cycle

---

### 3.3 Moment Detectors

**Module**: `neurosync/fusion/moment_detectors/`

**Pattern**: `BaseMomentDetector` (ABC) with tiered confidence:

```python
class BaseMomentDetector(ABC):
    def detect(self, state: FusionState) -> Optional[MomentDetectionResult]:
        # Step 1: Primary detection (REQUIRED -- always runs)
        primary = self.detect_primary(state)     # webcam + behavioral
        if primary is None:
            return None

        # Step 2: Optional EEG enhancement
        eeg_boost = 0.0
        if state.eeg is not None and state.eeg.quality >= 0.6:
            eeg_boost = self.detect_eeg_enhancement(state)  # 0.0 - 0.20

        total = min(1.0, primary + eeg_boost)

        # Step 3: Threshold gate (default 0.70)
        if total < self.base_threshold:
            return None

        return MomentDetectionResult(...)
```

**Tiered Confidence Ranges**:

| Tier              | Confidence | Signals Used                         |
|-------------------|------------|--------------------------------------|
| Behavioral only   | 0.40--0.70 | Response times, rewinds, idle        |
| + Webcam          | 0.60--0.85 | + Gaze, blink, expression, pose      |
| + NLP             | 0.65--0.90 | + Sentiment, complexity, confusion   |
| + EEG enhancement | 0.75--1.00 | + Alpha/beta/theta power (+0.20 max) |

**Implemented Detectors**:

| Detector               | ID  | Primary Signals                         | EEG Boost   |
|------------------------|-----|-----------------------------------------|-------------|
| `M01AttentionDetector` | M01 | Gaze off-screen, idle, low attention    | Alpha power (+0.12) |
| `M02CognitiveLoad`     | M02 | Response time increase, rewind bursts   | Theta/beta ratio    |
| `M10FatigueDetector`   | M10 | Session duration, blink rate, variance  | Alpha increase      |

Each detector reports which signal sources contributed via `signals_used`:
`{"webcam": bool, "behavioral": bool, "nlp": bool, "eeg": bool}`.

---

### 3.4 Signal Collectors

**Module**: `neurosync/behavioral/`, `neurosync/webcam/`, `neurosync/nlp/`, `neurosync/eeg/`

```
+---------------------+   +---------------------+
| AsyncEventCollector |   | WebcamProcessor     |
| (always active)     |   | (optional)          |
|                     |   |                     |
| - record_event()    |   | - MediaPipe face    |
| - record_question() |   | - Gaze tracking     |
| - record_video()    |   | - Blink detection   |
| - record_idle()     |   | - Expression recog. |
| - record_text()     |   | - Pose/fidget       |
| - asyncio.Queue     |   | - rPPG (secondary)  |
+---------------------+   +---------------------+

+---------------------+   +---------------------+
| NLPPipeline         |   | EEGCoordinator      |
| (optional)          |   | (optional)          |
|                     |   |                     |
| - Sentiment         |   | - Hardware lifecycle|
| - Complexity (FK)   |   | - Quality gating    |
| - Confusion detect  |   | - Graceful degrade  |
| - Keyword extract   |   | - Mock device avail.|
| - Topic drift       |   | - alpha/beta/theta  |
+---------------------+   +---------------------+
```

**Behavioral** (`neurosync/behavioral/collector.py`):
- Always active.  Receives events from the frontend via FastAPI.
- Events validated with Pydantic, persisted to SQLite, pushed to `asyncio.Queue`.
- Tracks response times, rewind counts, idle periods, answer accuracy.

**Webcam** (`neurosync/webcam/`):
- Optional.  Uses MediaPipe Face Mesh for landmark detection.
- Signals: gaze direction, blink rate (EAR threshold 0.20), expression
  classification, pose/fidget variance, remote PPG (secondary).
- Fusion: rolling window of 30 frames, 1-second aggregation interval.
- Injected into behavioral collector via `inject_webcam_signal()`.

**NLP** (`neurosync/nlp/pipeline.py`):
- Optional.  Runs on student text responses.
- Processors: sentiment, Flesch-Kincaid complexity, confusion keyword detector,
  keyword extraction, topic drift detection.
- Thresholds: frustration < -0.30, confusion > 0.50, topic drift < 0.40.

**EEG** (`neurosync/eeg/coordinator.py`):
- 100% optional.  Disabled by default (`EEG_ENABLED=false`).
- Quality-gated: signals ignored when quality < 0.6.
- Graceful degradation: `NullSession`-style -- returns `None`, never crashes.
- Provides: alpha, beta, theta, gamma power + frontal asymmetry.
- Mock device included for testing and demos.

---

### 3.5 Intervention Generator

**Module**: `neurosync/interventions/generator.py` -- class `InterventionGenerator`

Generates natural-language intervention content for detected moments.

```
InterventionGenerator.generate(type, context)
  |
  +---> 1. Cache lookup (SHA-256 key)
  |         Hit? --> return cached GeneratedContent
  |
  +---> 2. Cost limit check
  |         Exceeded? --> template fallback
  |
  +---> 3. Rate limit check (60 req/min)
  |         Exceeded? --> template fallback (unless priority=critical)
  |
  +---> 4. Build prompt (6 prompt builders)
  |         simplify | explain | misconception | rescue | plateau | application
  |
  +---> 5. LLM call (Groq or OpenAI) with exponential backoff
  |         Retries: 3 attempts, 2^n second backoff
  |
  +---> 6. Parse response --> GeneratedContent
  |
  +---> 7. Cache result
  |
  +---> On any failure --> FallbackTemplates.generate()
```

**Cache Key Generation**:
```python
combined = f"{intervention_type}:{json.dumps(context, sort_keys=True)}"
key = hashlib.sha256(combined.encode()).hexdigest()
```

**Prompt Builders** (in `neurosync/interventions/prompts/`):
- `SimplifyPrompts` -- reduce complexity while maintaining accuracy
- `ExplainPrompts` -- zero-prior-knowledge explanations with examples
- `MisconceptionPrompts` -- non-judgmental misconception correction
- `RescuePrompts` -- frustration recovery with fresh perspectives
- `PlateauPrompts` -- alternative teaching methods and analogies
- `ApplicationPrompts` -- genuine understanding questions, not recall

**Fallback Templates** (`neurosync/interventions/templates/fallbacks.py`):
Pre-written responses used when LLM is unavailable, rate-limited, or over budget.

---

### 3.6 Spaced Repetition Engine

**Module**: `neurosync/spaced_repetition/`

Implements exponential forgetting curve fitting to schedule optimal review times.

**Forgetting Curve Model**:
```
R(t) = R0 * exp(-t / tau)

Where:
  R(t) = retention at time t (days)
  R0   = initial retention (fitted, 0.5--1.0)
  tau  = decay constant (fitted, 0.1--30.0 days)
```

**Fitting** (`forgetting_curve/fitter.py`):
- Primary: `scipy.optimize.curve_fit` with bounded parameters.
- Fallback: log-linear regression when scipy fails.
- Default: `tau = 3.0 days`, `R0 = 0.95` when fewer than 3 data points.
- R-squared goodness-of-fit reported as confidence.

**Scheduling** (`scheduler.py`):
- Review threshold: retention = 0.70
- Safety buffer: 1.0 day before predicted threshold crossing
- First review: 2 hours after mastery

**Timing Optimization** (`timing/`):
- `CircadianOptimizer` -- identifies peak performance hours from session history
- `SleepWindow` -- avoids scheduling during estimated sleep (10 PM default)
- `SessionPlanner` -- plans review sessions within optimal windows

**Quiz Generation** (`quiz/`):
- Adaptive difficulty based on current retention
- 3 questions per review session, 60 seconds per question
- `DifficultyAdapter` adjusts based on performance

---

### 3.7 Knowledge Graph

**Module**: `neurosync/knowledge/`

Neo4j-backed concept prerequisite tracking with graceful offline degradation.

**Graph Manager** (`graph_manager.py`):
- Connection retry: 3 attempts with 1-second delay
- `NullSession` pattern: when Neo4j is offline, all queries return safe defaults
- Thread-safe Cypher execution with automatic error recovery

**Schema** (Cypher):
```
(:Student)-[:HAS_MASTERY]->(:Mastery)-[:OF_CONCEPT]->(:Concept)
(:Concept)-[:PREREQUISITE_OF]->(:Concept)
(:Concept)-[:PART_OF]->(:Topic)
```

**Detectors** (`knowledge/detectors/`):
- `GapDetector` -- finds prerequisite concepts with mastery < 0.40
- `MasteryChecker` -- evaluates current segment mastery
- `Mirror` -- detects confidence collapse (mastery drop >= 25% in 5 minutes)

**Mastery Scoring**:
- Correct answer: +0.15 (with +0.05 speed bonus if < 5 seconds)
- Incorrect answer: -0.10
- Daily decay: -0.02 per day (forgetting curve)
- Range: 0.0 to 1.0

---

### 3.8 Provider Abstraction

**LLM Factory** (`neurosync/llm/factory.py`):

```
LLMProviderFactory.create_provider()
  |
  +---> Try preferred (env LLM_PROVIDER, default "groq")
  |       Groq: llama-3.3-70b-versatile (FREE)
  |       OpenAI: gpt-4o
  |
  +---> If failed + fallback enabled:
  |       Try alternative provider
  |
  +---> If none available:
          raise RuntimeError
```

- `BaseLLMProvider` (ABC) defines the provider interface
- `GroqProvider` -- Groq API (OpenAI-compatible SDK, free tier)
- `OpenAIProvider` -- OpenAI API (gpt-4o / gpt-4-turbo)
- Factory pattern with automatic fallback: Groq -> OpenAI or OpenAI -> Groq

**TTS Factory** (`neurosync/tts/factory.py`):

- `BaseTTSProvider` (ABC) defines the TTS interface
- `GTTSProvider` -- Google Text-to-Speech (free, default)
- OpenAI TTS available via `TTS_PROVIDER=openai` environment variable
- Always falls back to gTTS (zero-cost guarantee)

---

## 4. Data Flow

### 4.1 Real-Time Detection Cycle (250 ms)

```
Student Interaction
       |
       v
+------------------+     +------------------+     +------------------+
| Electron UI      | --> | FastAPI Backend   | --> | AsyncEventCollector|
| (click/answer/   |     | (HTTP + WS)      |     | validate + persist |
|  rewind/idle)    |     |                  |     | to SQLite + Queue  |
+------------------+     +------------------+     +------------------+
                                                          |
                                                          v
                                                  +------------------+
                                                  | Signal Processors|
                                                  | (behavioral,     |
                                                  |  webcam, NLP)    |
                                                  +--------+---------+
                                                           |
                                   BehavioralSignals + WebcamSignals + NLPSignals
                                                           |
                                                           v
                                                  +------------------+
                                                  | FusionCoordinator|
                                                  | Build FusionState|
                                                  +--------+---------+
                                                           |
                                                           v
                                                  +------------------+
                                                  | FusionGraph      |
                                                  | 8 agents parallel|
                                                  | asyncio.gather() |
                                                  +--------+---------+
                                                           |
                                             InterventionProposal[]
                                                           |
                                                  +--------+---------+
                                                  | Cooldown Filter  |
                                                  | Conflict Resolve |
                                                  | Prioritize (max 2)|
                                                  +--------+---------+
                                                           |
                                                           v
                                                  +------------------+
                                                  | InterventionGen  |
                                                  | (Groq LLM +     |
                                                  |  SHA-256 cache)  |
                                                  +--------+---------+
                                                           |
                                                           v
                                                  +------------------+
                                                  | WebSocket push   |
                                                  | to Electron UI   |
                                                  +------------------+
```

### 4.2 Content Generation Flow

```
User uploads PDF
       |
       v
POST /content/upload
       |
       v
ContentPipeline.process_pdf()
       |
       +-- Stage 1-3: Parse, clean, analyze (local, no API)
       |
       +-- Stage 4: Extract concepts (Groq LLM, chunked)
       |
       +-- Stage 5-11: Generate all formats (parallel where possible)
       |       |
       |       +-- Slides (PPTX, local)
       |       +-- Scripts (Groq LLM)
       |       +-- Audio (gTTS, free)
       |       +-- Video (Pillow + ffmpeg, local)
       |       +-- Story (Groq LLM)
       |       +-- Quiz (Groq LLM)
       |       +-- Notes (Markdown, local)
       |
       v
PipelineResult (paths to all generated files)
       |
       v
Progress updates via WebSocket (ProgressTracker)
```

---

## 5. Key Design Decisions

### 5.1 Tiered Confidence Detection

**Problem**: Traditional systems require all sensors to be present, limiting
deployment to lab environments.

**Decision**: Primary detection uses only behavioral signals (always available).
Each additional signal layer (webcam, NLP, EEG) increases confidence but is
never required.

**Implementation**:
- `BaseMomentDetector.detect()` runs `detect_primary()` unconditionally.
- `detect_eeg_enhancement()` is called only when `state.eeg` is not None and
  `quality >= 0.6`.
- EEG boost capped at +0.20 to prevent over-reliance on noisy data.
- Base threshold: 0.70 (configurable per detector).

**Result**: System works in any environment -- from a basic laptop with no
webcam to a full lab setup with EEG headset.

### 5.2 $0 Cost Architecture

**Problem**: OpenAI API costs ($0.01-0.03/1K tokens) make per-student
deployment unsustainable for educational institutions.

**Decision**: Default to Groq (free tier, llama-3.3-70b-versatile) for all
LLM calls and gTTS (free) for text-to-speech.

**Implementation**:
- `LLMProviderFactory` defaults to `LLM_PROVIDER=groq`.
- `TTSProviderFactory` defaults to `TTS_PROVIDER=gtts`.
- `ContentPipeline` uses OpenAI-compatible SDK pointed at Groq endpoint.
- OpenAI remains available as a fallback (`enable_fallback=True`).
- Intervention generator adds SHA-256 caching to minimize redundant calls.

**Result**: Complete course generation and real-time tutoring at zero
marginal cost per student.

### 5.3 Graceful Degradation

**Problem**: External dependencies (Neo4j, webcam hardware, EEG device) are
unreliable in field deployments.

**Decision**: Every external dependency has a null-object fallback.

| Component   | Fallback                                          |
|-------------|---------------------------------------------------|
| Neo4j       | `NullSession` -- queries return empty lists        |
| EEG         | `EEGCoordinator` returns `None`, detectors skip   |
| Webcam      | `WebcamSignals` is `Optional`, behavioral-only    |
| NLP         | `NLPSignals` is `Optional`, skipped if absent     |
| LLM (Groq)  | Falls back to OpenAI, then to template fallbacks  |
| TTS (gTTS)  | Always available (pure Python, no API key needed)  |
| scipy       | Log-linear regression fallback for curve fitting   |

### 5.4 Agent Isolation

**Problem**: A crashing agent must not bring down the entire fusion cycle.

**Decision**: `FusionGraph._run_agent()` wraps every agent in a try/except.
On failure, it returns an empty `AgentEvaluation` with the error logged.
`asyncio.gather()` runs all 8 agents in parallel; a single failure does not
block or delay other agents.

### 5.5 Intervention Throttling

**Problem**: Over-triggering interventions disrupts the learning flow.

**Decision**: Three-stage filtering after agent evaluation:
1. `CooldownTracker` -- per-moment cooldown (default 120s, frustration 300s).
2. `ConflictResolver` -- removes incompatible simultaneous interventions.
3. `InterventionPrioritizer` -- selects max 2 per cycle, ranked by urgency
   (critical > high > medium > low) and confidence.

---

## 6. Directory Structure

```
NeuroSync-AI/
|
+-- neurosync/                      # Python backend package
|   +-- api/                        # FastAPI application
|   |   +-- server.py               #   App factory, WebSocket, health
|   |   +-- routes/                 #   REST endpoints (session, signals, etc.)
|   |   +-- schemas/                #   Pydantic request/response models
|   |
|   +-- behavioral/                 # Behavioral signal collection (Step 1)
|   |   +-- collector.py            #   AsyncEventCollector (always active)
|   |   +-- signals.py              #   Signal aggregation
|   |   +-- moments.py              #   Behavioral moment helpers
|   |   +-- fusion.py               #   Behavioral signal fusion
|   |
|   +-- webcam/                     # Webcam signal processing (Step 2)
|   |   +-- mediapipe_processor.py  #   MediaPipe Face Mesh integration
|   |   +-- capture.py              #   Frame capture
|   |   +-- fusion.py               #   Webcam signal fusion
|   |   +-- injector.py             #   Inject webcam into behavioral
|   |   +-- signals/                #   Gaze, blink, expression, pose, rPPG
|   |
|   +-- knowledge/                  # Knowledge graph (Step 3)
|   |   +-- graph_manager.py        #   Neo4j driver + NullSession fallback
|   |   +-- schema.cypher           #   Graph schema definition
|   |   +-- detectors/              #   Gap, mastery, mirror (collapse)
|   |   +-- repositories/           #   Cypher query wrappers
|   |   +-- seeders/                #   Demo data population
|   |
|   +-- nlp/                        # NLP pipeline (Step 4)
|   |   +-- pipeline.py             #   Orchestrates all NLP processors
|   |   +-- processors/             #   Sentiment, complexity, confusion, etc.
|   |
|   +-- fusion/                     # Detection + fusion engine
|   |   +-- orchestrator.py         #   Top-level NeuroSyncOrchestrator
|   |   +-- coordinator.py          #   FusionCoordinator (250ms cycle)
|   |   +-- graph.py                #   FusionGraph (asyncio.gather)
|   |   +-- state.py                #   Pydantic v2 state models
|   |   +-- agents/                 #   8 LangGraph-style agents
|   |   |   +-- base_agent.py       #     BaseAgent ABC
|   |   |   +-- attention_agent.py  #     M01
|   |   |   +-- overload_agent.py   #     M02
|   |   |   +-- gap_agent.py        #     M03
|   |   |   +-- engagement_agent.py #     M06, M08
|   |   |   +-- fatigue_agent.py    #     M10
|   |   |   +-- memory_agent.py     #     M16
|   |   |   +-- misconception_agent.py #  M15
|   |   |   +-- plateau_agent.py    #     M22
|   |   +-- moment_detectors/       #   Tiered confidence detectors
|   |   |   +-- base_detector.py    #     BaseMomentDetector ABC
|   |   |   +-- m01_attention.py    #     Attention drop
|   |   |   +-- m02_cognitive_load.py #   Cognitive overload
|   |   |   +-- m10_fatigue.py      #     Fatigue detection
|   |   +-- decision/               #   Post-detection filtering
|   |       +-- cooldown.py         #     Per-moment cooldown tracking
|   |       +-- conflict_resolver.py#     Incompatible intervention removal
|   |       +-- prioritizer.py      #     Max-2 selection by urgency
|   |
|   +-- interventions/              # Intervention content generation
|   |   +-- generator.py            #   InterventionGenerator (main entry)
|   |   +-- cost_tracker.py         #   Per-session/lifetime cost limits
|   |   +-- cache/                  #   SHA-256 keyed response cache
|   |   +-- prompts/                #   6 prompt builder classes
|   |   +-- templates/              #   Static fallback templates
|   |
|   +-- content/                    # Content generation pipeline
|   |   +-- pipeline.py             #   ContentPipeline (11 stages)
|   |   +-- progress_tracker.py     #   WebSocket progress updates
|   |   +-- parsers/                #   PDF parser, text cleaner
|   |   +-- analyzers/              #   Structure, complexity, concepts
|   |   +-- generators/             #   Slides, scripts, quiz, story, video
|   |   +-- formats/                #   Markdown, slides, video, quiz, story
|   |   +-- tts/                    #   gTTS + OpenAI TTS adapters
|   |
|   +-- spaced_repetition/          # Spaced repetition engine
|   |   +-- scheduler.py            #   Review scheduling
|   |   +-- analytics.py            #   Retention analytics
|   |   +-- forgetting_curve/       #   Exponential curve fitter (scipy)
|   |   +-- timing/                 #   Circadian optimizer, sleep window
|   |   +-- quiz/                   #   Adaptive review quiz generation
|   |   +-- notifications/          #   Review reminders
|   |
|   +-- llm/                        # LLM provider abstraction
|   |   +-- factory.py              #   LLMProviderFactory
|   |   +-- base_provider.py        #   BaseLLMProvider ABC
|   |   +-- groq_provider.py        #   Groq (free, default)
|   |   +-- openai_provider.py      #   OpenAI (fallback)
|   |
|   +-- tts/                        # TTS provider abstraction
|   |   +-- factory.py              #   TTSProviderFactory
|   |   +-- base_provider.py        #   BaseTTSProvider ABC
|   |   +-- gtts_provider.py        #   gTTS (free, default)
|   |
|   +-- eeg/                        # Optional EEG integration
|   |   +-- coordinator.py          #   EEGCoordinator + MockDevice
|   |
|   +-- config/                     # Configuration and thresholds
|   |   +-- settings.py             #   All thresholds, provider config
|   |
|   +-- core/                       # Shared event models
|   +-- database/                   # SQLite manager + repositories
|   |   +-- manager.py              #   DatabaseManager (WAL mode)
|   |   +-- schema.sql              #   Table definitions
|   |   +-- repositories/           #   Events, sessions
|   |
|   +-- readiness/                  # Pre-lesson readiness protocol
|   +-- experiments/                # A/B testing framework
|   +-- utils/                      # Patent logger, helpers
|
+-- neurosync-ui/                   # Electron + React frontend
|   +-- electron/                   #   Electron main process
|   +-- src/                        #   React application
|   |   +-- App.tsx                 #     Root component
|   |   +-- components/             #     UI components
|   |   +-- hooks/                  #     Custom React hooks
|   |   +-- services/               #     API client services
|   |   +-- stores/                 #     Zustand state stores
|   |   +-- types/                  #     TypeScript type definitions
|   |   +-- utils/                  #     Frontend utilities
|   +-- tests/                      #   Vitest + Playwright tests
|   +-- package.json                #   React 18, Electron 28, Vite 5
|
+-- tests/                          # Python test suite (pytest)
+-- scripts/                        # CLI utilities and demos
+-- docs/                           # Documentation
+-- sample_content/                 # Example PDFs and outputs
```

---

## 7. Environment Variables

| Variable         | Default               | Purpose                              |
|------------------|-----------------------|--------------------------------------|
| `LLM_PROVIDER`   | `groq`               | LLM provider: `groq` or `openai`    |
| `GROQ_API_KEY`   | (none)               | Groq API key (free at console.groq.com) |
| `GROQ_MODEL`     | `llama-3.3-70b-versatile` | Groq model identifier           |
| `OPENAI_API_KEY` | (none)               | OpenAI API key (fallback)            |
| `TTS_PROVIDER`   | `gtts`               | TTS provider: `gtts` or `openai`    |
| `NEO4J_URI`      | `bolt://localhost:7687` | Neo4j connection URI              |
| `NEO4J_USER`     | `neo4j`              | Neo4j username                       |
| `NEO4J_PASSWORD` | `neurosync`          | Neo4j password                       |
| `EEG_ENABLED`    | `false`              | Enable EEG hardware integration      |
| `EEG_DEVICE`     | `mock`               | EEG device type                      |
| `DATABASE_PATH`  | `data/neurosync.db`  | SQLite database path                 |
| `LOG_LEVEL`      | `DEBUG`              | Logging verbosity                    |
