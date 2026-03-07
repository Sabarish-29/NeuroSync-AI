# NeuroSync AI — Q&A Preparation

Anticipated questions and prepared answers for hackathon judges.

---

## Technical Architecture

### Q: How does the real-time fusion engine work?

The fusion engine uses 8 parallel LangGraph agents running via `asyncio.gather()` on a 250ms cycle. Each agent receives a `FusionState` snapshot containing signals from all modalities (webcam, behavioral, NLP, knowledge graph, and optionally EEG). Agents independently evaluate their assigned learning moments and return detection results. A 4-stage conflict resolution pipeline then selects up to 2 non-conflicting interventions per cycle, prioritised by severity.

### Q: Why 22 learning moments instead of a simpler model?

Educational research identifies distinct failure modes — a student daydreaming (M01 Attention Drop) requires a fundamentally different intervention than a student who is engaged but confused (M02 Cognitive Overload) or frustrated (M07). Lumping these into "stuck" loses actionable signal. Each of our 22 moments maps to a specific, tested intervention strategy. However, only 5-7 moments account for ~80% of real detections; the rest handle rarer edge cases.

### Q: How do you handle latency for real-time detection?

Behavioral and webcam signals are computed locally (no API calls) using numpy/scipy rolling-window analysis. The fusion engine runs in-process via asyncio. Only the intervention *content generation* calls an external API (Groq), and that only fires when a moment is actually detected (not every 250ms). Groq inference typically completes in 300-800ms, well within our 2-second SLA.

### Q: What happens if the webcam is unavailable?

The system degrades gracefully. Every detector has a `detect_primary()` method that handles `webcam=None`. Behavioral signals alone (click patterns, rewinds, idle time, scroll velocity) provide 70-85% detection confidence for most moments. Webcam is listed as an optional enhancement source, not a hard requirement.

---

## AI / ML Questions

### Q: What models do you use and why?

- **Detection**: No ML models — the 22 detectors use hand-tuned weighted composite scoring with configurable thresholds. This is deliberate: interpretable rules let teachers understand *why* the system flagged a moment, and there is no training data bootstrapping problem.
- **Interventions**: Groq Llama 3.3 70B for generating personalised content (simplify, explain, rescue, etc.) with SHA-256 response caching and fallback templates.
- **Content Pipeline**: Same Groq model for concept extraction, script generation, quiz generation, and story creation from source PDFs.
- **TTS**: Google gTTS (free) for narrated video audio.

### Q: Why not use a fine-tuned model for detection?

Three reasons: (1) We have no labelled student interaction dataset to train on. (2) Hand-tuned detectors are fully interpretable — we can explain exactly which signals triggered a detection. (3) The weighted scoring approach lets teachers/researchers adjust thresholds per context without retraining.

### Q: How accurate is the detection?

In our controlled desk-testing (not a formal study), the attention drop (M01) and cognitive overload (M02) detectors correctly identified simulated failure states in >90% of manually-triggered test scenarios. Formal validation requires an IRB-approved student trial, which is in our roadmap. The experiments framework is already built and supports A/B testing with control/treatment conditions.

### Q: What is the tiered confidence system?

Each detector has two stages:
1. **Primary detection** (always runs): Uses webcam + behavioral signals → 70-85% confidence.
2. **EEG enhancement** (optional): If an EEG headset is connected with good signal quality (>60%), brainwave features (alpha, beta, theta power) can boost confidence by up to +15%.

The system works fully without EEG hardware. EEG is an optional enhancement, never a requirement.

---

## Data & Privacy

### Q: What student data do you collect?

We track: (1) anonymised interaction events (clicks, scroll, timing), (2) webcam-derived attention scores (raw video is NOT stored — only numeric scores from MediaPipe), (3) NLP analysis scores from chat messages, (4) knowledge mastery levels in the Neo4j graph. All data is local to the institution's deployment. No data leaves the server.

### Q: Is the webcam data stored?

No. The webcam module processes frames in real-time using MediaPipe face mesh and outputs numeric attention/expression scores. Raw video frames are never saved to disk or transmitted. The FusionState only contains float scores like `attention_score=0.73, frustration_boost=0.12`.

### Q: How do you handle GDPR / data protection?

All processing is local (on-premise deployment). Student IDs are anonymised UUIDs. No biometric data is stored (webcam scores are derived metrics, not images). Data retention policies are configurable per institution. The experiments framework includes consent tracking.

---

## Cost & Scalability

### Q: What does it cost to run?

$0 in API costs. After migrating to Groq Llama 3.3 70B (free tier) + gTTS (free), the only costs are server hosting. Content generation for a 15-minute course uses ~50K Groq tokens, well within the free tier. Intervention generation caches responses with SHA-256 keys, so repeated patterns cost nothing.

### Q: How does it compare to the original OpenAI costs?

Before migration: $5-10 per course (GPT-4 + OpenAI TTS). After migration: $0 per course (Groq + gTTS). The factory pattern and adapter interfaces mean switching back to OpenAI requires changing one environment variable (`LLM_PROVIDER=openai`).

### Q: Can it handle 1000 concurrent students?

The fusion engine is per-student and lightweight (numpy/scipy, no GPU needed). The bottleneck is LLM intervention generation, which is cached and rate-limited. For 1000 students, we would need: (1) horizontal scaling of the FastAPI backend, (2) Groq's paid tier for higher rate limits, and (3) a shared Redis cache instead of in-memory SQLite. The architecture supports this — the provider factory and cache manager are already abstracted.

---

## Content Generation

### Q: How does the PDF-to-course pipeline work?

11 async stages: (1) PDF parsing and text extraction, (2) concept identification via LLM, (3) concept graph building, (4) script generation per concept, (5) narration script polishing, (6) TTS audio generation, (7) slide content generation, (8) video frame rendering at 1920x1080/24fps via MoviePy, (9) audio-video muxing, (10) quiz bank generation, (11) story/notes generation. Stages run concurrently where possible using asyncio.

### Q: What formats does it output?

Five formats from a single PDF: (1) narrated video (MP4, 1920x1080, 24fps), (2) slide deck (PPTX), (3) Markdown notes, (4) narrative story, (5) JSON quiz bank with answers and distractors.

### Q: How long does generation take?

Approximately 8-12 minutes per 15-minute course on a standard development machine, dominated by LLM inference time for chunked concept extraction and script generation.

---

## Spaced Repetition

### Q: How does the forgetting curve work?

We fit per-student forgetting curves to the model R(t) = R0 * exp(-t/tau) using `scipy.optimize.curve_fit`. R0 is the initial retention level and tau is the personalised decay constant. When a student's predicted retention for a concept drops below a configurable threshold (default 70%), the system schedules a review. If insufficient data points exist for curve fitting, we fall back to log-linear regression with a default 7-day half-life.

### Q: Why not use SM-2 or Anki's algorithm?

SM-2 uses fixed ease factors and doesn't model individual students' actual forgetting curves. Our approach fits a continuous exponential model to each student's review performance data, providing more accurate predictions. The R-squared confidence score tells us when the curve fit is reliable vs when to fall back to the simpler model.

---

## Testing & Quality

### Q: How many tests do you have?

470+ automated tests across 12 modules using pytest. Key coverage: behavioral signals (41 tests), fusion engine (33 tests), knowledge graph (43 tests), content pipeline (42 tests), interventions (24 tests), spaced repetition (22 tests), tiered detection (45 tests across 4 test files). All tests pass on every commit.

### Q: How do you test without real students?

We use synthetic FusionState objects with controlled signal values. For example, to test attention drop detection, we create a state with `attention_score=0.10, off_screen_duration_ms=5000, idle_frequency=1.5` and verify the M01 detector fires with the expected confidence level. The experiments framework also includes a simulation mode for generating synthetic student interaction traces.

---

## Differentiation

### Q: How is this different from existing adaptive learning platforms?

Most adaptive platforms (Khan Academy, ALEKS, Knewton) adapt based on quiz performance — *after* the student has already failed. NeuroSync detects failure *as it's happening* using real-time behavioral and visual signals, intervening *before* the student gives up. We also detect 22 specific failure modes vs the typical 3-5 "stuck states," enabling targeted interventions rather than generic hints.

### Q: What about Coursera's or edX's recommendation systems?

Those operate at the course/module level: "you might like this course." NeuroSync operates at the 250ms signal level within a single lesson: "you seem confused about photosynthesis right now, here's a simpler explanation." Different problem, different time scale.
