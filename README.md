# NeuroSync AI v5.1

> A multi-modal adaptive learning system that addresses 22 specific learning failure moments using behavioral signals, webcam, NLP, and knowledge graphs.

## Current Status: Step 1 — Behavioral Signal Collector

The foundation layer: raw event capture → signal processing → moment detection. Powers M07 (Frustration), M08 (Insight), M10 (Fatigue), M14 (Pseudo-understanding), M20 (Dopamine rewards) from day one.

## Quick Start (for teammates)

```bash
# 1. Clone the repo
git clone https://github.com/Sabarish-29/NeuroSync-AI.git
cd NeuroSync-AI

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialise the database
python scripts/init_db.py

# 5. Run all tests
pytest tests/ -v --cov=neurosync --cov-report=term-missing

# 6. Run the simulation (proves everything works)
python scripts/simulate_session.py

# 7. (Optional) Interactive demo
python scripts/demo_collector.py
```

## Project Structure

```
neurosync/
├── config/          # Settings and thresholds
├── core/            # Pydantic event models and constants
├── behavioral/      # Signal processors, moment detectors, fusion engine
├── database/        # SQLite schema, manager, repositories
tests/               # 25+ unit tests (pytest + pytest-asyncio)
scripts/             # Init DB, simulation, interactive demo
```

## Tech Stack (Step 1)

- **Python 3.11+**
- **SQLite** (WAL mode, thread-safe)
- **Pydantic v2** (data validation)
- **scipy/numpy** (signal processing)
- **asyncio** (non-blocking event collection)
- **loguru** (structured logging)
- **pytest** (testing)

## The 22 Learning Moments

| ID | Moment | Step 1 Status |
|----|--------|---------------|
| M07 | Silent frustration / pre-dropout | ✅ Built |
| M08 | Insight moment | ✅ Built (behavioral proxy) |
| M10 | Mental fatigue | ✅ Built |
| M14 | Pseudo-understanding | ✅ Built |
| M20 | Dopamine crash | ✅ Built |
| M01-M06, M09, M11-M13, M15-M19, M21-M22 | Coming in Steps 2-12 | Schema ready |

## License

MIT
