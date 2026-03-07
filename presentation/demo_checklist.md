# NeuroSync AI — Pre-Demo Checklist

Validate every item before the live demonstration.

---

## Environment Setup

- [ ] Python 3.11+ installed and on PATH
- [ ] Node.js 18+ installed (for Electron UI)
- [ ] All pip dependencies installed (`pip install -r requirements.txt`)
- [ ] All npm dependencies installed (`cd neurosync-ui && npm install`)
- [ ] `GROQ_API_KEY` environment variable set and valid
- [ ] Neo4j running locally (optional — system degrades gracefully)
- [ ] Webcam accessible (optional — behavioral-only mode works)

## Source Content

- [ ] 5 source PDFs present in `sample_content/source_pdfs/`
  - [ ] photosynthesis.pdf
  - [ ] newtons_laws.pdf
  - [ ] cell_structure.pdf
  - [ ] chemical_bonds.pdf
  - [ ] mughal_empire.pdf
- [ ] Run `python scripts/verify_sample_content.py` — all checks pass

## Generated Content (if pre-generating)

- [ ] Run `python scripts/generate_sample_content.py` for at least 1 course
- [ ] Verify output in `sample_content/generated/<course_id>/`
- [ ] Open generated video (MP4) and confirm audio plays
- [ ] Open generated slides (PPTX) and confirm content renders
- [ ] Open generated quiz (JSON) and spot-check 2-3 questions

## Test Suite

- [ ] Run `pytest` from project root — 470+ tests pass
- [ ] No import errors or missing dependency warnings
- [ ] Run `python -m neurosync.utils.config_validator` — status is "ready" or "degraded"

## System Validator

- [ ] Run system validator: `python -c "from neurosync.utils.config_validator import SystemValidator; SystemValidator.print_status_report()"`
- [ ] Core checks pass: groq=True, behavioral=True
- [ ] Optional checks noted: webcam, eeg, neo4j (failures OK)

## Intervention Engine

- [ ] Run `python scripts/demo_interventions.py`
- [ ] All 6 intervention types generate output (LLM or fallback)
- [ ] Verify output is coherent and grade-appropriate
- [ ] Note which mode is active (Groq / Fallback)

## Electron UI (if demoing the frontend)

- [ ] `cd neurosync-ui && npm run dev` starts without errors
- [ ] Dashboard loads in the Electron window
- [ ] Real-time charts render (even with mock data)
- [ ] Knowledge graph visualization renders (D3.js)

## Network & Hardware

- [ ] Stable internet connection (for Groq API calls)
- [ ] Backup: fallback templates work offline (test by unsetting GROQ_API_KEY)
- [ ] Demo laptop charged or plugged in
- [ ] Screen resolution set to 1920x1080 for screenshots/recording
- [ ] Close unnecessary applications to avoid memory pressure

## Presentation Materials

- [ ] Slides created per `docs/presentation_slides_outline.md`
- [ ] Q&A responses reviewed (`docs/QA_RESPONSES.md`)
- [ ] Demo script rehearsed at least once
- [ ] Timer set for presentation slot (typically 10-15 min)

## Backup Plans

- [ ] If Groq is down: intervention engine falls back to templates automatically
- [ ] If webcam fails: system runs in behavioral-only mode (70-85% confidence)
- [ ] If Neo4j is down: knowledge graph features skip gracefully
- [ ] If network is down: pre-generated content can still be shown from disk
- [ ] If full demo fails: slides + screenshots demonstrate all features

---

## Quick Smoke Test (Run 5 min Before Demo)

```bash
# 1. Verify tests pass
pytest --tb=short -q 2>&1 | tail -5

# 2. Verify source PDFs
python scripts/verify_sample_content.py

# 3. Verify system health
python -c "from neurosync.utils.config_validator import SystemValidator; SystemValidator.print_status_report()"

# 4. Verify interventions work
python scripts/demo_interventions.py 2>&1 | tail -20
```

If all 4 commands succeed, you are ready to demo.
