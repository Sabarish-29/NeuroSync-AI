# NeuroSync AI - Installation Guide

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Backend, ML pipeline |
| Node.js | 18+ | Frontend build |
| pip | latest | Python package management |
| Git | 2.0+ | Version control |
| Webcam | any | Attention detection (optional) |
| Neo4j | 5.x | Knowledge graph (optional) |

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Sabarish-29/NeuroSync-AI.git
cd NeuroSync-AI

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — at minimum, set GROQ_API_KEY
```

## Environment Configuration

Create a `.env` file in the project root:

```bash
# ── Required ─────────────────────────────────────────────
GROQ_API_KEY=gsk_your_key_here       # Free at console.groq.com

# ── LLM Provider (default: groq) ────────────────────────
LLM_PROVIDER=groq                    # Options: groq, openai
# OPENAI_API_KEY=sk-proj-...         # Only if LLM_PROVIDER=openai

# ── TTS Provider (default: gtts) ────────────────────────
TTS_PROVIDER=gtts                    # Options: gtts, openai

# ── Neo4j (optional) ────────────────────────────────────
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password

# ── EEG (optional, disabled by default) ─────────────────
# EEG_ENABLED=false
# EEG_DEVICE_TYPE=mock
```

### Getting a Groq API Key (Free)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (no credit card required)
3. Navigate to API Keys
4. Create a new key
5. Copy the key starting with `gsk_` into your `.env`

## Verify Installation

```bash
# Run the full test suite
pytest tests/ -v

# Expected: 470+ tests passing

# Run system health check
python -c "from neurosync.utils.config_validator import SystemValidator; SystemValidator.print_status_report()"
```

## Frontend Setup (Optional)

```bash
cd neurosync-ui
npm install
npm run dev        # Starts Vite dev server + Electron
```

## Neo4j Setup (Optional)

The knowledge graph features require Neo4j but the system degrades
gracefully without it.

### Docker (recommended)

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:5
```

### Native Install

```bash
# Ubuntu/Debian
sudo apt-get install neo4j

# macOS
brew install neo4j

# Start
neo4j start
```

Then update `.env`:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

## Sample Content Generation

```bash
# 1. Create source PDFs (5 educational topics)
python scripts/create_source_pdfs.py

# 2. Verify PDFs
python scripts/verify_sample_content.py

# 3. Generate courses (requires GROQ_API_KEY)
python scripts/generate_sample_content.py

# 4. Verify generated content
python scripts/verify_sample_content.py --full
```

## Running the Demo

```bash
# Intervention engine demo (6 scenarios)
python scripts/demo_interventions.py

# Full demo walkthrough
# See docs/DEMO_SCRIPT.md
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'cv2'`

```bash
pip install opencv-python-headless
```

### `GROQ_API_KEY not set`

Ensure your `.env` file contains a valid Groq key. Verify:

```bash
python -c "import os; print(os.getenv('GROQ_API_KEY', 'NOT SET'))"
```

### Neo4j connection refused

The system works without Neo4j. If you need it, verify it's running:

```bash
neo4j status
# or
docker ps | grep neo4j
```

### Tests failing with import errors

Ensure you're running from the project root and dependencies are installed:

```bash
cd /path/to/NeuroSync-AI
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
NeuroSync-AI/
├── neurosync/              # Python backend
│   ├── api/                # FastAPI server
│   ├── behavioral/         # Signal collection
│   ├── config/             # Settings
│   ├── content/            # PDF-to-course pipeline
│   ├── eeg/                # Optional EEG coordinator
│   ├── fusion/             # 8-agent fusion + moment detectors
│   ├── interventions/      # LLM-powered interventions
│   ├── knowledge_graph/    # Neo4j integration
│   ├── llm/                # Provider abstraction (Groq/OpenAI)
│   ├── nlp/                # Text analysis
│   ├── spaced_repetition/  # Forgetting curves
│   ├── tts/                # Provider abstraction (gTTS/OpenAI)
│   └── webcam/             # MediaPipe face/gaze
├── neurosync-ui/           # React + Electron frontend
├── scripts/                # Utilities and demos
├── tests/                  # 470+ pytest tests
├── docs/                   # Documentation
├── sample_content/         # Source PDFs and generated courses
└── requirements.txt        # Python dependencies
```
