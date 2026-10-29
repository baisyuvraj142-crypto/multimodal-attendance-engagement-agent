# Software Requirements Specification (SRS)

**Project:** Multimodal Attendance & Engagement Agent (EduSense AI)  
**Prepared by:** Yuvraj Singh Bais  
**Version:** 1.0 | **Date:** 29 October 2026  
**Platform:** SkillWallet – Generative AI with Google Cloud  

---

## 1. Introduction

### 1.1 Purpose
This document specifies the requirements for the Multimodal Attendance & Engagement Agent, an AI-powered, privacy-preserving classroom intelligence system. It combines computer vision, audio signal processing and rule-based agent reasoning to automatically track attendance, estimate engagement, and give instructors context-aware teaching suggestions.

### 1.2 Problem Statement
Attendance in schools and training centres is still manual or limited to biometric systems. These are slow, error-prone and say nothing about attention, interaction or session effectiveness. Instructors need a decision-support tool that goes beyond presence detection.

### 1.3 Scope
The system will:
- Detect and track participants from a live webcam or recorded classroom video.
- Mark attendance using presence duration, not a single-frame detection.
- Analyse audio (noise level, speech activity) and fuse it with visual signals.
- Compute a time-based engagement score using transparent, adjustable rules.
- Generate instructor-facing teaching suggestions and student-facing session summaries.
- Present results in a web dashboard with exportable PDF and CSV reports.

**Out of scope:** grading or evaluating students, automated disciplinary decisions, permanent storage of raw video or audio, and multi-camera or multi-room deployment.

### 1.4 Definitions
- **Presence duration:** cumulative time a tracked face is visible in a session.
- **Engagement score:** 0–100 value derived from visual and audio indicators over a time window.
- **Fusion:** timestamp-aligned combination of vision and audio features.
- **Agent:** the rule-based reasoning layer (optionally LLM-assisted) that turns signals into insights.

---

## 2. Overall Description

### 2.1 Product Perspective
A three-tier web application: a React frontend that captures webcam and microphone, a FastAPI backend that processes frames and audio, and a SQLite database for session data. An optional Streamlit dashboard offers an alternate analytics view.

### 2.2 Users
- **Instructor:** runs sessions, views live status, suggestions, and reports.
- **Student:** views own reflective session summary (no grades, no ranking).
- **Administrator / Mentor:** reviews the project, demo and repository.

### 2.3 Operating Environment
Windows 10/11, macOS Monterey+, or Ubuntu 20.04+; Python 3.8+ (3.10 recommended); modern Chrome, Edge or Firefox; webcam and microphone; Intel i5 8th gen or better, 8 GB RAM minimum.

### 2.4 Design Constraints and Assumptions
- Privacy first: process locally, store only derived metrics, never raw media.
- Suggestions are advisory and non-prescriptive.
- Core features must work without internet. Any cloud LLM is optional and must have a rule-based fallback.
- Face detection uses OpenCV Haar cascades (with MediaPipe available); tracking uses DeepSORT; optional recognition uses DeepFace.

---

## 3. System Architecture

### 3.1 Components
1. **Frontend (React + Vite):** live session view, teacher profile, analytics and reports, audio capture component.
2. **Backend (FastAPI + Uvicorn):** REST and WebSocket endpoints, core services.
3. **Vision module:** camera service, face detector, tracker, presence-based attendance.
4. **Audio module:** audio analyzer at 16 kHz for noise and speech activity.
5. **Fusion and engagement engine:** merges signals, computes engagement scores.
6. **Agent layer:** recommendations engine (rules), optional LLM insight generator (Groq) with fallback.
7. **Analytics service:** session trends, student summaries, teacher profile.
8. **Persistence:** SQLAlchemy over SQLite.
9. **Optional Streamlit dashboard.**

---

## 4. Functional Requirements

### 4.1 Environment and Setup (Epic 1)
- **FR-1.1:** Provide `requirements.txt` listing fastapi, uvicorn, opencv-python, numpy, pandas, python-multipart, websockets, sqlalchemy, groq, python-dotenv.
- **FR-1.2:** Provide a documented virtual-environment setup and a smoke test that imports all key libraries and starts the backend.

### 4.2 Vision Module (Epic 2)
- **FR-2.1:** Capture frames from a webcam or a pre-recorded video file.
- **FR-2.2:** Detect faces per frame and return bounding boxes with confidence.
- **FR-2.3:** Assign each face a persistent ID across frames (DeepSORT) that survives brief occlusion and head movement.
- **FR-2.4:** Output structured data: participant ID, timestamp, position.
- **FR-2.5:** Attendance is marked Present only when cumulative presence exceeds a configurable threshold (default 60 seconds); intermittent appearances accumulate.
- **FR-2.6:** Store attendance logs with participant ID, first seen, last seen and presence duration.

### 4.3 Audio Module (Epic 3)
- **FR-3.1:** Capture microphone audio in the browser and stream it to the backend, or extract audio from a recorded video.
- **FR-3.2:** Normalise sampling rate (16 kHz) and channels, and split into fixed windows.
- **FR-3.3:** Compute noise level (dB), speech versus silence ratio and sound activity pattern per window.
- **FR-3.4:** Classify each window as silence, background noise or active speech, and store with timestamps.

### 4.4 AI Implementation (Epic 4)
- **FR-4.1:** Multimodal agent consumes vision and audio outputs for each session.
- **FR-4.2:** Fusion aligns signals by timestamp (presence, movement, inactivity, noise, speech).
- **FR-4.3:** Engagement scoring uses transparent, configurable thresholds and is computed at regular intervals (for example every 10 seconds) to produce a temporal profile.
- **FR-4.4:** Scoring parameters are editable in a config file without code changes.

### 4.5 Analytics and Recommendations (Epic 5)
- **FR-5.1:** Detect sustained disengagement, attention drops, high-interaction periods and noisy intervals.
- **FR-5.2:** Produce teaching suggestions as alert, warning or info items (for example suggest an interactive activity after a long low-engagement stretch).
- **FR-5.3:** Optional LLM-generated insight text; if the LLM is unavailable or no API key exists, fall back to rule-based text.
- **FR-5.4:** Teacher profile shows effectiveness score, trend, class history comparison and strengths.
- **FR-5.5:** Student session summary shows attendance duration, engagement consistency and notable activity trends, written reflectively, without grades.
- **FR-5.6:** Session trend API aggregates metrics by timestamp for charting.

### 4.6 Interface, Testing and Deployment (Epic 6)
- **FR-6.1:** Dashboard (dark theme) shows session timer, students present, live video with overlays, emotion or engagement live panel, audio context, AI suggestion box and AI insights.
- **FR-6.2:** Analytics page shows attention trend and engagement distribution over time, with PDF and CSV export.
- **FR-6.3:** Optional Streamlit dashboard shows attendance records, engagement timelines, suggestions and analytics.
- **FR-6.4:** Edge-case validation covering low light, background noise, partial occlusion, short appearances and intermittent audio.
- **FR-6.5:** Application is deployed publicly and the source is on GitHub.

### 4.7 Session Management
- **FR-7.1:** Start and end session controls; each session has a unique ID.
- **FR-7.2:** Sessions are persisted and listable with date, duration and summary.

---

## 5. Non-Functional Requirements
- **NFR-1 Privacy:** no raw video or audio is stored; only derived metrics. Camera and microphone permission is requested explicitly and a visible indicator shows when capture is active.
- **NFR-2 Ethics:** the system never grades or ranks individuals for punishment. If the live leaderboard is kept, it must be optional and use anonymised IDs; recommended default is OFF to respect the no peer comparison principle.
- **NFR-3 Performance:** at least 10 FPS processing on an i5 8th gen with 8 GB RAM; dashboard latency under 1 second.
- **NFR-4 Reliability:** graceful degradation if audio, camera or LLM fails.
- **NFR-5 Explainability:** every score and suggestion can be traced to the rule and data that triggered it.
- **NFR-6 Portability:** one-command setup on Windows, macOS and Linux.
- **NFR-7 Security:** secrets in `.env`, never committed; CORS restricted; file upload size and type validated.
- **NFR-8 Maintainability:** modular services, type hints, docstrings, README and basic unit tests.

---

## 6. Acceptance Criteria
1. Attendance is marked only after the presence threshold is met.
2. Engagement timeline renders with both vision and audio contributing.
3. At least three distinct teaching suggestion types are generated from test data.
4. Student summary contains no grades or rankings.
5. PDF and CSV exports download correctly.
6. App runs from a fresh clone using the README steps.
7. Public demo URL and GitHub repository are live and linked on SkillWallet.
