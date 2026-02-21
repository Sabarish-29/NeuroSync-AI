# NeuroSync AI v5.1

> A multi-modal adaptive learning system that detects 22 specific learning failure moments in real-time using behavioral signals, webcam vision, NLP, and knowledge graphs. Delivers personalized AI interventions within 2 seconds.

## Features

- **22 Learning Moment Detection** - Real-time identification of attention drops, cognitive overload, frustration, fatigue, and 18 more moments
- **Multimodal Signal Fusion** - Combines webcam, behavioral, NLP, knowledge graph, and timing signals every 250ms using LangGraph with 8 specialized AI agents
- **AI-Powered Interventions** - Generates personalized content simplifications, explanations, and rescue strategies using Groq Llama 3.3 70B (FREE)
- **Automated Course Generation** - Converts PDF textbooks to narrated videos, slide decks, quiz banks, and story explanations in 12 minutes
- **Spaced Repetition** - Personalized forgetting curves fit to each student's retention data with adaptive review scheduling
- **Pre-Lesson Readiness** - Anxiety detection with guided breathing exercises and readiness checks
- **Knowledge Graph** - Neo4j-powered concept prerequisite tracking and mastery visualization
- **Zero Operating Cost** - Runs entirely on free APIs (Groq + gTTS + local Neo4j)

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Sabarish-29/NeuroSync-AI.git
cd NeuroSync-AI

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your Groq API key (free at console.groq.com)

# 5. Initialize the database
python scripts/init_db.py

# 6. Run all tests
pytest tests/ -v --cov=neurosync --cov-report=term-missing

# 7. Start the API server
python neurosync/api/server.py

# 8. Start the frontend (separate terminal)
cd neurosync-ui
npm install
npm run dev
```

## FREE API Configuration

NeuroSync runs entirely on free APIs - no credit card required.

### 1. Groq (FREE LLM)
```bash
# Sign up at https://console.groq.com (no credit card)
# Get API key from https://console.groq.com/keys
```

### 2. gTTS (FREE Text-to-Speech)
Already included in dependencies. No signup needed.

### 3. Neo4j (FREE Local)
```bash
# Ubuntu/Debian
sudo apt-get install neo4j

# macOS
brew install neo4j

# Start server
neo4j start
```

### Configure `.env`
```bash
# LLM Provider (FREE)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here

# TTS Provider (FREE)
TTS_PROVIDER=gtts

# Neo4j Local (FREE)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

Want better quality? Add OpenAI as fallback:
```bash
LLM_PROVIDER=groq           # Use Groq (FREE) first
OPENAI_API_KEY=sk-proj-...  # Fallback to OpenAI if needed
```

## Architecture

```
neurosync/
├── api/              # FastAPI server with WebSocket support
├── behavioral/       # Signal processors, moment detectors, fusion engine
├── config/           # Settings, thresholds, and provider configuration
├── content/          # PDF parsing, concept extraction, content generation
├── core/             # Pydantic event models and constants
├── database/         # SQLite schema, manager, repositories
├── experiments/      # A/B testing framework (E1-E5)
├── interventions/    # GPT-4/Groq intervention generator with caching
├── knowledge_graph/  # Neo4j concept graph with prerequisites
├── langgraph/        # 8-agent fusion engine with LangGraph orchestration
├── llm/              # Provider abstraction (Groq, OpenAI, factory)
├── nlp/              # Text analysis pipeline
├── readiness/        # Pre-lesson anxiety detection + breathing exercises
├── spaced_repetition/# Personalized forgetting curves + review scheduling
├── tts/              # Provider abstraction (gTTS, factory)
├── video/            # Video rendering with MoviePy
└── webcam/           # MediaPipe-based gaze and expression detection

neurosync-ui/         # React + TypeScript frontend
├── src/
│   ├── components/
│   │   ├── teacher/  # Dashboard, ContentLibrary, UploadPDF, Analytics
│   │   ├── student/  # LearningInterface, VideoPlayer, InterventionOverlay
│   │   └── shared/   # Navigation, ProgressBar, ErrorAlert, MomentBadge
│   ├── hooks/        # useFusionLoop, useInterventions, useWebcam, useKeyboardShortcuts
│   └── stores/       # Zustand session state management
└── electron/         # Electron main process

scripts/              # Utilities and demos
tests/                # 400+ tests (pytest + vitest)
docs/                 # Migration guide, content guide, slides outline
```

## The 22 Learning Moments

| ID | Moment | Detection Method |
|----|--------|------------------|
| M01 | Attention Drop | Webcam gaze tracking |
| M02 | Cognitive Overload | Response time + rewind patterns |
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

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM | Groq Llama 3.3 70B | FREE |
| TTS | gTTS (Google) | FREE |
| Knowledge Graph | Neo4j (local) | FREE |
| Backend | Python 3.11+, FastAPI, asyncio | -- |
| Frontend | React 18, TypeScript, Vite | -- |
| Desktop | Electron 28 | -- |
| Database | SQLite (WAL mode) | -- |
| Signal Processing | scipy, numpy | -- |
| Webcam | MediaPipe | -- |
| Video | MoviePy | -- |
| Fusion | LangGraph | -- |
| Testing | pytest, vitest, Playwright | -- |

## Testing

```bash
# Run all Python tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=neurosync --cov-report=term-missing

# Run frontend tests
cd neurosync-ui && npm test

# Run specific test file
pytest tests/test_llm_providers.py -v
```

**Test counts by component:**
- Behavioral Signal Collector: 41 tests
- Webcam Vision Layer: 20 tests
- Knowledge Graph: 43 tests
- NLP Pipeline: 39 tests
- LangGraph Fusion Engine: 33 tests
- Intervention Generator: 24 tests
- Content Generation: 42 tests
- Spaced Repetition: 22 tests
- Pre-Lesson Readiness: 18 tests
- UI Components: 42 tests
- Experiments Framework: 28 tests
- Provider Migration: 51 tests
- **Total: 400+ tests**

## Demo

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the complete 5-minute demo walkthrough with Q&A preparation.

### Sample Content

1. Create source PDFs following [docs/SAMPLE_CONTENT_GUIDE.md](docs/SAMPLE_CONTENT_GUIDE.md)
2. Generate courses: `python scripts/generate_sample_content.py`
3. Verify output: `python scripts/verify_sample_content.py`

## Project Status

| Step | Component | Status |
|------|-----------|--------|
| 1 | Behavioral Signal Collector | Complete |
| 2 | Webcam Vision Layer | Complete |
| 3 | Knowledge Graph (Neo4j) | Complete |
| 4 | NLP Pipeline | Complete |
| 5 | LangGraph Fusion Engine | Complete |
| 6 | GPT-4 Intervention Generator | Complete |
| 7 | Content Generation Pipeline | Complete |
| 8 | Spaced Repetition Engine | Complete |
| 9 | Pre-Lesson Readiness Protocol | Complete |
| 10 | Electron Desktop UI | Complete |
| 11 | Experiments Framework | Complete |
| 12 | API Server & Integration | Complete |
| 13 | Free API Migration (Groq + gTTS) | Complete |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run all tests (`pytest tests/ -v`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

MIT
