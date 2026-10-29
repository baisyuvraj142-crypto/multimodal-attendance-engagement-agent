# EduSense AI — Multimodal Classroom Attendance & Engagement Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-cyan.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-emerald.svg)](https://fastapi.tiangolo.com/)
[![React + Vite](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-violet.svg)](https://vitejs.dev/)

**EduSense AI** is an AI-powered, privacy-preserving multimodal classroom intelligence system prepared for **SkillWallet – Generative AI with Google Cloud**. It combines computer vision (face detection & persistent tracking), audio signal processing (16 kHz noise decibels & speech activity), and transparent rule-based agent reasoning with optional Groq LLM assistance.

---

## Key Features

- **Presence-Based Attendance (Not Single-Frame):** Accurately marks attendance only after cumulative presence duration exceeds a configurable threshold (default: 60s). Handles intermittent absences seamlessly.
- **Multimodal Signal Fusion:** Aligns visual attention (gaze proxy, face symmetry) with acoustic context (active dialogue vs. ambient chatter vs. lecture silence).
- **Explainable Engagement Scoring (0–100):** Transparent, configurable weighted formula with explainability breakdown for instructors.
- **Pedagogical AI Co-Pilot:** Real-time actionable teaching suggestions (`alert`, `warning`, `info`) and LLM session insights (with automatic rule-based fallback).
- **Ethical & Non-Punitive:** Strictly zero grades, marks, or peer ranking. Generates constructive, reflective student session summaries.
- **Export & Analytics:** One-click download of PDF summary reports and CSV attendance ledgers.
- **Dual Interfaces:** Modern dark-theme React dashboard and an alternative Streamlit dashboard.

---

## Project Structure

```text
edusense-ai/
├── backend/
│   ├── main.py                     # FastAPI REST & WebSocket endpoints
│   ├── requirements.txt            # Python dependencies
│   ├── smoke_test.py               # System & library verification test
│   ├── .env.example                # Configurable environment template
│   ├── core/
│   │   ├── config.py               # Transparent settings & weights
│   │   ├── database.py             # SQLite & SQLAlchemy models
│   │   ├── camera_service.py       # Frame decoding, preprocessing & overlays
│   │   ├── face_detection.py       # OpenCV Haar Cascade / DNN face detector
│   │   ├── face_recognition.py     # Re-identification feature extractor
│   │   ├── tracking.py             # Multi-Object Tracker (DeepSORT / IoU)
│   │   ├── audio_analysis.py       # 16 kHz acoustic dB & speech activity
│   │   ├── fusion.py               # Timestamp-aligned multimodal fusion
│   │   ├── engagement.py           # Composite engagement scoring engine
│   │   ├── recommendations_engine.py # Rule-based pedagogy recommendations
│   │   ├── ai_suggestions.py       # Orchestration layer
│   │   ├── llm_insights.py         # Groq LLM integration with fallback
│   │   ├── analytics_service.py    # Trends, PDF & CSV export generators
│   │   └── teacher_profiles.py     # Effectiveness metrics & benchmarks
│   └── tests/
│       ├── test_core.py            # Unit tests for acceptance criteria
│       └── run_tests.py            # Zero-dependency test suite runner
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx                 # Top-level state & navigation
│       ├── index.css               # Glassmorphic dark theme styles
│       └── components/
│           ├── AudioCapture.jsx    # Web Audio 16 kHz streaming & meter
│           ├── LiveSession.jsx     # Live stream, HUD & recommendations
│           ├── Analytics.jsx       # Charts, PDF/CSV export & student notes
│           └── TeacherProfile.jsx  # Pedagogical strengths & trend stats
├── streamlit_app/
│   └── dashboard.py                # Alternate Streamlit analytics view
├── docs/
│   ├── SRS.md                      # Full Software Requirements Specification
│   ├── architecture.md             # System architecture & Mermaid diagrams
│   └── uat_checklist.md            # Acceptance criteria & edge case tests
├── Dockerfile                      # Production Docker container definition
├── docker-compose.yml              # Local multi-service orchestration
├── LICENSE                         # MIT License
└── README.md
```

---

## Quick Start Guide

### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

#### Run Smoke Test:
```bash
python smoke_test.py
```

#### Run Unit Tests (Verifying All 5 Acceptance Criteria):
```bash
python tests/run_tests.py
```

#### Launch Backend Server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

### 2. Frontend Setup (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

### 3. Alternative Streamlit Dashboard (Optional)
```bash
streamlit run streamlit_app/dashboard.py
```
Open `http://localhost:8501`.

---

## Docker Deployment

To launch the full stack locally via Docker Compose:
```bash
docker-compose up --build
```

---

## Configuration (`.env`)

| Variable | Default | Purpose |
|:---|:---|:---|
| `PRESENCE_THRESHOLD_SECONDS` | `60.0` | Minimum seconds for "Present" mark |
| `GROQ_API_KEY` | *(empty)* | Optional Groq API key for LLM insights |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Hosted Groq model identifier |
| `DATABASE_URL` | `sqlite:///./edusense.db` | SQLAlchemy connection string |
| `ATTENTION_WEIGHT` | `0.45` | Formula weight for visual attention |
| `MOVEMENT_WEIGHT` | `0.20` | Formula weight for body stability |
| `AUDIO_WEIGHT` | `0.35` | Formula weight for vocal interaction |

---

## Acceptance Criteria Summary

1. **Presence Logic:** Attendance is marked `Present` only when cumulative duration $\ge$ threshold.
2. **Multimodal Fusion:** Engagement combines visual attention, movement, and acoustic state.
3. **Suggestion Diversity:** Produces `alert`, `warning`, and `info` recommendation categories.
4. **Ethical Non-Punitive:** Student summaries contain zero grades or rankings.
5. **PDF & CSV Export:** Verified downloadable reports from REST endpoints.

---

## License

Released under the [MIT License](LICENSE).
