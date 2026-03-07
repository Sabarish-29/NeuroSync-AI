# NeuroSync AI v5.1

> Real-time adaptive learning system that detects 22 specific learning failure moments using multimodal signal fusion (webcam, behavioral, NLP, knowledge graph, optional EEG). Delivers personalized AI interventions within 2 seconds at zero operating cost.

## Key Features

- **22 Learning Moment Detection** -- Identifies attention drops, cognitive overload, frustration, fatigue, and 18 more failure modes every 250ms using 8 parallel LangGraph agents
- **Tiered Confidence System** -- Primary detection (webcam + behavioral, 70-85% confidence) with optional EEG enhancement (+10-15%), no hardware dependency
- **Automated Course Generation** -- PDF to narrated video, slides, quiz, and notes in 10 minutes using Groq + gTTS
- **Zero Operating Cost** -- Runs entirely on free APIs (Groq Llama 3.3 70B + gTTS + local Neo4j)
- **AI-Powered Interventions** -- Generates personalized simplifications, explanations, and rescue strategies with SHA-256 response caching
- **Spaced Repetition** -- Per-student forgetting curves fit via scipy exponential decay model
- **Knowledge Graph** -- Neo4j concept prerequisites with mastery tracking
- **Patent-Pending Innovations** -- 3 provisional patents filed (22-moment taxonomy, content pipeline, EEG quality gating)

## Quick Start

```bash
# Clone and install
git clone https://github.com/Sabarish-29/NeuroSync-AI.git
cd NeuroSync-AI
pip install -r requirements.txt

# Configure (only GROQ_API_KEY required -- free at console.groq.com)
cp .env.example .env
# Edit .env: set GROQ_API_KEY=gsk_your_key_here

# Verify installation
pytest tests/ -v            # 490+ tests
python -c "from neurosync.utils.config_validator import SystemValidator; SystemValidator.print_status_report()"
```

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed setup instructions.

## Configuration

NeuroSync runs on free APIs -- no credit card required.

```bash
# .env (minimum configuration)
GROQ_API_KEY=gsk_your_key_here   # Free at console.groq.com
LLM_PROVIDER=groq                # Default: groq (free)
TTS_PROVIDER=gtts                # Default: gtts (free)

# Optional
# NEO4J_URI=bolt://localhost:7687
# EEG_ENABLED=false
# OPENAI_API_KEY=sk-...          # Fallback if Groq unavailable
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│    PRESENTATION    React 18 + TypeScript + Electron 28      │
├─────────────────────────────────────────────────────────────┤
│    APPLICATION     FastAPI + WebSocket (250ms push)          │
├─────────────────────────────────────────────────────────────┤
│    DETECTION       22 Moment Detectors + 8-Agent Fusion      │
├─────────────────────────────────────────────────────────────┤
│    SIGNALS         Webcam | Behavioral | NLP | EEG (opt)     │
├─────────────────────────────────────────────────────────────┤
│    CONTENT         PDF → Video/Slides/Quiz/Notes ($0)        │
├─────────────────────────────────────────────────────────────┤
│    DATA            Neo4j | SQLite | File System              │
└─────────────────────────────────────────────────────────────┘
```

```
neurosync/
├── api/                # FastAPI server + WebSocket
├── behavioral/         # Signal collectors, event processing
├── config/             # Settings, thresholds, provider config
├── content/            # 11-stage PDF-to-course pipeline
├── eeg/                # Optional EEG coordinator (disabled by default)
├── experiments/        # A/B testing framework (E1-E5)
├── fusion/             # LangGraph 8-agent engine + moment detectors
│   └── moment_detectors/  # M01, M02, M10 (tiered confidence)
├── interventions/      # Groq-powered generator + caching
├── knowledge_graph/    # Neo4j concept graph
├── llm/                # Provider abstraction (Groq/OpenAI factory)
├── nlp/                # Text complexity + sentiment analysis
├── spaced_repetition/  # Forgetting curves + review scheduling
├── tts/                # Provider abstraction (gTTS/OpenAI factory)
├── utils/              # Config validator, patent logger
├── video/              # MoviePy video rendering
└── webcam/             # MediaPipe gaze + expression detection

neurosync-ui/src/
├── components/         # teacher/ student/ shared/ visualizations/
├── hooks/              # useFusionLoop, useWebcam, useKeyboardShortcuts
├── stores/             # Zustand state management
└── utils/              # Error handling utilities

docs/                   # Architecture, installation, patents, demo
scripts/                # Content generation, verification, demos
tests/                  # 490+ automated tests
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed component documentation.

## The 22 Learning Moments

| ID | Moment | Detection Method |
|----|--------|------------------|
| M01 | Attention Drop | Webcam gaze + behavioral idle |
| M02 | Cognitive Overload | Rewind bursts + facial tension + NLP confusion |
| M03 | Boredom | Behavioral disengagement signals |
| M04 | Confusion | NLP analysis + expression detection |
| M05 | Response Slowdown | Timing analysis |
| M06 | Guessing | Fast-answer pattern detection |
| M07 | Frustration | Rewind bursts + click rage |
| M08 | Insight Moment | Engagement spike detection |
| M09 | Fatigue | Session duration + signal degradation |
| M10 | Rewind Burst | Video interaction patterns |
| M11 | Idle | Inactivity detection |
| M12 | Mastery Ready | Consistent high performance |
| M13 | Achievement | Milestone completion |
| M14 | Zone of Proximal Development | Difficulty calibration |
| M15 | Emotional Spike | Expression analysis |
| M16 | Help Seeking | Behavioral pattern recognition |
| M17 | Engagement Peak | Multimodal engagement score |
| M18 | Distraction | Webcam + behavioral fusion |
| M19 | Misconception | NLP response analysis |
| M20 | Plateau | Learning curve stagnation |
| M21 | Review Needed | Spaced repetition triggers |
| M22 | Discomfort | Multimodal stress signals |

M01, M02, and M10 have full tiered confidence implementations with patent-documented thresholds. Remaining moments use the same `BaseMomentDetector` framework.

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM | Groq Llama 3.3 70B | FREE |
| TTS | gTTS (Google) | FREE |
| Knowledge Graph | Neo4j (local) | FREE |
| Backend | Python 3.11+, FastAPI, asyncio | -- |
| Frontend | React 18, TypeScript, Vite | -- |
| Desktop | Electron 28 | -- |
| Fusion | LangGraph (8 agents) | -- |
| Webcam | MediaPipe | -- |
| Signal Processing | scipy, numpy | -- |
| Database | SQLite (WAL mode) | -- |
| Video | MoviePy | -- |
| Testing | pytest, vitest, Playwright | -- |

## Testing

```bash
pytest tests/ -v                    # Run all tests
pytest tests/ --cov=neurosync       # With coverage
cd neurosync-ui && npm test         # Frontend tests
```

490+ automated tests across all components. Key areas:
- Behavioral signals, webcam, NLP pipeline
- Fusion engine, moment detectors (tiered confidence)
- Content generation pipeline
- Knowledge graph, spaced repetition
- Provider migration (Groq/gTTS)
- Patent logging integration

## Demo

See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for the 5-minute presentation with timing marks and backup plans.

```bash
# Generate sample courses
python scripts/create_source_pdfs.py
python scripts/generate_sample_content.py

# Run intervention demo
python scripts/demo_interventions.py

# Verify everything
python scripts/verify_sample_content.py --full
```

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and component details |
| [INSTALLATION.md](docs/INSTALLATION.md) | Setup and configuration guide |
| [PATENT_CLAIMS.md](docs/PATENT_CLAIMS.md) | 3 provisional patent claims |
| [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | 5-minute hackathon demo script |
| [QA_RESPONSES.md](docs/QA_RESPONSES.md) | 20+ anticipated judge Q&As |
| [PRESENTATION_SLIDES.md](docs/PRESENTATION_SLIDES.md) | 12-slide deck content |
| [SAMPLE_CONTENT_GUIDE.md](docs/SAMPLE_CONTENT_GUIDE.md) | Content creation guide |

## Project Status

| Phase | Component | Status |
|-------|-----------|--------|
| 1 | Groq + gTTS migration ($0 cost) | Complete |
| 2 | Tiered confidence detection (22 moments) | Complete |
| 3 | Sample content and demo materials | Complete |
| 4 | Patent documentation and production polish | Complete |
| -- | Behavioral Signal Collector | Complete |
| -- | Webcam Vision Layer (MediaPipe) | Complete |
| -- | Knowledge Graph (Neo4j) | Complete |
| -- | NLP Pipeline | Complete |
| -- | LangGraph Fusion Engine (8 agents) | Complete |
| -- | Intervention Generator (Groq) | Complete |
| -- | Content Generation Pipeline | Complete |
| -- | Spaced Repetition Engine | Complete |
| -- | Pre-Lesson Readiness Protocol | Complete |
| -- | Electron Desktop UI | Complete |
| -- | Experiments Framework (A/B testing) | Complete |
| -- | API Server and Integration | Complete |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Run all tests (`pytest tests/ -v`)
4. Commit your changes
5. Push and open a Pull Request

## License

MIT
