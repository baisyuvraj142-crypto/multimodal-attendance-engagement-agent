# EduSense AI — System Architecture & Data Flow

## 1. High-Level Architecture Overview

EduSense AI is designed as a three-tier, privacy-preserving multimodal intelligence platform:
1. **Frontend Presentation Tier:** React (Vite) Single Page Application capturing webcam and audio locally in browser, rendering live detection bounding boxes, engagement HUDs, and reflective summaries.
2. **Backend Processing Tier:** FastAPI + Uvicorn server running computer vision (OpenCV face detection, DeepSORT multi-object tracking, presence accumulation), audio DSP (16 kHz normalization, RMS decibels, zero-crossing rate VAD), multimodal fusion, and the rule-based reasoning engine with optional Groq LLM fallback.
3. **Storage & Analytics Tier:** SQLite with SQLAlchemy ORM storing derived non-punitive metrics, attendance logs, and pedagogical alert histories. Alternate Streamlit dashboard for administrative analytics.

```mermaid
graph TD
    subgraph Browser ["Frontend Browser (Client-Side)"]
        Cam["Webcam Capture (Canvas 10-15 FPS)"]
        Mic["Microphone Stream (Web Audio 16 kHz)"]
        UI["React Dashboard (Live HUD, Analytics, Reports)"]
    end

    subgraph Backend ["FastAPI Backend Services"]
        WS["WebSocket Handlers (/ws/live, /ws/video, /ws/audio)"]
        REST["REST API Controllers (/api/sessions, /api/teachers)"]
        
        subgraph VisionEngine ["Vision Pipeline"]
            FD["Face Detection (OpenCV Haar/DNN)"]
            Tracker["Multi-Object Tracker (DeepSORT/IoU + Kalman)"]
            Presence["Presence Duration Accumulator"]
        end

        subgraph AudioEngine ["Audio DSP Pipeline"]
            Norm["16 kHz Resampling & Windowing"]
            VAD["RMS dB & Zero-Crossing VAD"]
            State["Classifier: Silence / Noise / Speech"]
        end

        Fusion["Multimodal Timestamp Alignment & Fusion"]
        Score["Engagement Scoring Engine (Configurable Weights)"]
        Rules["Rule-Based Recommendations Engine"]
        LLM["Groq LLM Insight Generator (with Graceful Fallback)"]
    end

    subgraph Storage ["Persistence Tier"]
        DB[("SQLite Database via SQLAlchemy")]
        PDF["PDF & CSV Export Generators"]
    end

    subgraph StreamlitApp ["Streamlit Alternative Analytics"]
        ST["Streamlit UI (dashboard.py)"]
    end

    Cam -->|Base64 JPEG| WS
    Mic -->|16-bit PCM Chunks| WS
    WS --> VisionEngine
    WS --> AudioEngine

    VisionEngine --> Fusion
    AudioEngine --> Fusion
    Fusion --> Score
    Score --> Rules
    Rules --> LLM
    Rules --> DB
    Presence --> DB
    Score --> DB

    LLM --> WS
    Rules --> WS
    Score --> WS
    WS -->|Live Telemetry Sync| UI

    REST --> DB
    REST --> PDF
    UI --> REST
    ST --> REST
```

---

## 2. Multimodal Signal Fusion & Engagement Formula

The platform aligns visual attention and acoustic environment into unified temporal snapshots:

$$E = \frac{w_{\text{att}} \cdot A + w_{\text{mov}} \cdot M + w_{\text{aud}} \cdot S_{\text{audio}}}{w_{\text{att}} + w_{\text{mov}} + w_{\text{aud}}}$$

Where:
- $w_{\text{att}} = 0.45$: Weight for frontal gaze and visual attentiveness
- $w_{\text{mov}} = 0.20$: Weight for natural, non-restless body stability
- $w_{\text{aud}} = 0.35$: Weight for acoustic context (active speech participation vs. noise vs. silence)

All parameters are transparently defined in `backend/core/config.py` and editable via `.env` without modifying code.

---

## 3. Privacy-First Boundary (NFR-1)

```mermaid
flowchart LR
    A["Raw Camera Pixels"] --> B["In-Memory Frame Buffer"]
    C["Raw Microphone Audio"] --> D["In-Memory PCM Buffer"]
    
    B --> E["Face Bounding Box & Gaze Proxy"]
    D --> F["RMS Decibels & Speech Ratio"]
    
    E --> G["Derived Metrics Only"]
    F --> G
    
    G --> H[("SQLite Database")]
    
    subgraph PrivacyZone ["DISCARDED IMMEDIATELY"]
        B
        D
    end
```

Raw audio waveforms and raw video frames exist only momentarily in volatile RAM buffers during analysis and are immediately discarded. No video or audio files are ever written to disk.
