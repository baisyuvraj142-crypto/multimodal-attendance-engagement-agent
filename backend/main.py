import uuid
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import init_db, get_db, SessionModel, PersonModel, PersonMetricModel, AudioMetricModel, SuggestionModel
from core.face_detection import FaceDetector
from core.tracking import MultiObjectTracker
from core.camera_service import CameraService
from core.audio_analysis import AudioAnalyzer
from core.fusion import MultimodalFusion
from core.engagement import EngagementEngine
from core.recommendations_engine import RecommendationsEngine
from core.ai_suggestions import AISuggestionService
from core.analytics_service import AnalyticsService
from core.teacher_profiles import TeacherProfileService

# Initialize database schema
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multimodal Classroom Attendance and Engagement Intelligence Agent"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared active session processors in-memory
class ActiveSessionContext:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.tracker = MultiObjectTracker(max_age=35, min_hits=2, iou_threshold=0.25)
        self.detector = FaceDetector()
        self.audio_analyzer = AudioAnalyzer()
        self.engagement_engine = EngagementEngine()
        self.ai_service = AISuggestionService()
        self.last_audio_data = {"noise_db": -50.0, "speech_ratio": 0.0, "state": "silence"}

active_sessions: Dict[str, ActiveSessionContext] = {}

def get_or_create_context(session_id: str) -> ActiveSessionContext:
    if session_id not in active_sessions:
        active_sessions[session_id] = ActiveSessionContext(session_id)
    return active_sessions[session_id]

# --- Pydantic Request Models ---
class StartSessionRequest(BaseModel):
    title: Optional[str] = "Classroom Lecture"
    teacher_id: Optional[str] = "teacher_1"

# --- REST Endpoints ---

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "llm_ready": bool(settings.GROQ_API_KEY)
    }

@app.post("/api/sessions/start")
def start_session(req: StartSessionRequest, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())[:8]
    new_session = SessionModel(
        id=session_id,
        teacher_id=req.teacher_id,
        title=req.title,
        start_time=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    # Initialize session context
    active_sessions[session_id] = ActiveSessionContext(session_id)
    
    return {
        "id": new_session.id,
        "title": new_session.title,
        "teacher_id": new_session.teacher_id,
        "start_time": new_session.start_time.isoformat(),
        "status": "active"
    }

@app.post("/api/sessions/{session_id}/end")
def end_session(session_id: str, db: Session = Depends(get_db)):
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    session_obj.end_time = datetime.utcnow()
    db.commit()

    # Flush all participants' final presence to database
    ctx = active_sessions.get(session_id)
    if ctx:
        records = ctx.tracker.get_all_records(presence_threshold=settings.PRESENCE_THRESHOLD_SECONDS)
        for rec in records:
            p_obj = db.query(PersonModel).filter(
                PersonModel.id == rec["person_id"],
                PersonModel.session_id == session_id
            ).first()
            if not p_obj:
                p_obj = PersonModel(
                    id=rec["person_id"],
                    session_id=session_id,
                    label=rec["label"],
                    first_seen=datetime.fromisoformat(rec["first_seen"]),
                    last_seen=datetime.fromisoformat(rec["last_seen"]),
                    presence_seconds=rec["presence_seconds"],
                    attendance_status=rec["attendance_status"]
                )
                db.add(p_obj)
            else:
                p_obj.presence_seconds = rec["presence_seconds"]
                p_obj.attendance_status = rec["attendance_status"]
                p_obj.last_seen = datetime.fromisoformat(rec["last_seen"])
        db.commit()

    duration_sec = (session_obj.end_time - session_obj.start_time).total_seconds() if session_obj.end_time else 0
    return {
        "id": session_obj.id,
        "status": "completed",
        "start_time": session_obj.start_time.isoformat(),
        "end_time": session_obj.end_time.isoformat(),
        "duration_seconds": round(duration_sec, 1)
    }

@app.get("/api/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(SessionModel).order_by(SessionModel.start_time.desc()).all()
    results = []
    for s in sessions:
        duration = (s.end_time - s.start_time).total_seconds() if s.end_time else 0
        total_present = db.query(PersonModel).filter(
            PersonModel.session_id == s.id,
            PersonModel.attendance_status == "Present"
        ).count()
        results.append({
            "id": s.id,
            "title": s.title,
            "teacher_id": s.teacher_id,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "duration_seconds": round(duration, 1),
            "students_present": total_present
        })
    return results

@app.get("/api/sessions/{session_id}")
def get_session_details(session_id: str, db: Session = Depends(get_db)):
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    duration = (session_obj.end_time - session_obj.start_time).total_seconds() if session_obj.end_time else 0
    return {
        "id": session_obj.id,
        "title": session_obj.title,
        "teacher_id": session_obj.teacher_id,
        "start_time": session_obj.start_time.isoformat() if session_obj.start_time else None,
        "end_time": session_obj.end_time.isoformat() if session_obj.end_time else None,
        "duration_seconds": round(duration, 1)
    }

@app.get("/api/sessions/{session_id}/attendance")
def get_session_attendance(session_id: str, db: Session = Depends(get_db)):
    # Check if active in memory
    ctx = active_sessions.get(session_id)
    if ctx:
        records = ctx.tracker.get_all_records(presence_threshold=settings.PRESENCE_THRESHOLD_SECONDS)
        return {"session_id": session_id, "attendance": records}

    # Otherwise query database
    persons = db.query(PersonModel).filter(PersonModel.session_id == session_id).all()
    return {
        "session_id": session_id,
        "attendance": [
            {
                "person_id": p.id,
                "label": p.label,
                "first_seen": p.first_seen.isoformat(),
                "last_seen": p.last_seen.isoformat(),
                "presence_seconds": p.presence_seconds,
                "attendance_status": p.attendance_status
            } for p in persons
        ]
    }

@app.get("/api/sessions/{session_id}/trends")
def get_session_trends(session_id: str, db: Session = Depends(get_db)):
    trends = AnalyticsService.get_session_trends(db, session_id)
    student_summaries = AnalyticsService.get_student_reflective_summaries(db, session_id)
    trends["student_summaries"] = student_summaries
    return trends

@app.get("/api/sessions/{session_id}/suggestions")
def get_session_suggestions(session_id: str, db: Session = Depends(get_db)):
    suggestions = db.query(SuggestionModel).filter(
        SuggestionModel.session_id == session_id
    ).order_by(SuggestionModel.timestamp.desc()).all()
    return {
        "session_id": session_id,
        "suggestions": [
            {
                "id": s.id,
                "type": s.type,
                "rule_id": s.rule_id,
                "message": s.message,
                "timestamp": s.timestamp.isoformat()
            } for s in suggestions
        ]
    }

@app.get("/api/teachers/{teacher_id}/profile")
def get_teacher_profile(teacher_id: str, db: Session = Depends(get_db)):
    return TeacherProfileService.get_profile(teacher_id=teacher_id)

@app.get("/api/sessions/{session_id}/report.pdf")
def download_pdf_report(session_id: str, db: Session = Depends(get_db)):
    pdf_bytes = AnalyticsService.export_pdf(db, session_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=edusense_session_{session_id}_report.pdf"}
    )

@app.get("/api/sessions/{session_id}/export.csv")
def download_csv_export(session_id: str, db: Session = Depends(get_db)):
    csv_data = AnalyticsService.export_csv(db, session_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=edusense_session_{session_id}.csv"}
    )

# --- WebSocket Endpoints ---

@app.websocket("/ws/video")
async def websocket_video_endpoint(websocket: WebSocket, session_id: str = "default"):
    await websocket.accept()
    ctx = get_or_create_context(session_id)
    db = SessionLocal()
    try:
        while True:
            data = await websocket.receive_json()
            frame_b64 = data.get("frame")
            if not frame_b64:
                continue

            frame = CameraService.decode_base64_frame(frame_b64)
            if frame is None:
                continue

            # Preprocess
            frame = CameraService.preprocess_frame(frame)
            detections = ctx.detector.detect(frame)
            active_tracks = ctx.tracker.update(detections, presence_threshold=settings.PRESENCE_THRESHOLD_SECONDS)
            overlay_b64 = CameraService.render_overlay(frame, active_tracks)

            await websocket.send_json({
                "type": "video_update",
                "tracks": active_tracks,
                "overlay_frame": f"data:image/jpeg;base64,{overlay_b64}",
                "count": len(active_tracks)
            })
    except WebSocketDisconnect:
        pass
    finally:
        db.close()

@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket, session_id: str = "default"):
    await websocket.accept()
    ctx = get_or_create_context(session_id)
    db = SessionLocal()
    try:
        while True:
            data = await websocket.receive_json()
            audio_raw = data.get("audio")
            if audio_raw:
                samples = ctx.audio_analyzer.parse_audio_chunk(audio_raw)
                audio_res = ctx.audio_analyzer.analyze_window(samples)
                ctx.last_audio_data = audio_res

                # Persist audio metric snapshot
                metric = AudioMetricModel(
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                    noise_db=audio_res["noise_db"],
                    speech_ratio=audio_res["speech_ratio"],
                    state=audio_res["state"]
                )
                db.add(metric)
                db.commit()

                await websocket.send_json({
                    "type": "audio_update",
                    "metrics": audio_res
                })
    except WebSocketDisconnect:
        pass
    finally:
        db.close()

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket, session_id: str = "default"):
    """
    Unified multimodal real-time stream.
    Receives frame + audio from frontend, fuses signals, updates engagement,
    evaluates rule-based recommendations, and generates live insights.
    """
    await websocket.accept()
    ctx = get_or_create_context(session_id)
    db = SessionLocal()
    try:
        while True:
            packet = await websocket.receive_json()
            frame_b64 = packet.get("frame")
            audio_chunk = packet.get("audio")

            # 1. Process Audio if present
            if audio_chunk:
                samples = ctx.audio_analyzer.parse_audio_chunk(audio_chunk)
                ctx.last_audio_data = ctx.audio_analyzer.analyze_window(samples)

            # 2. Process Vision
            active_tracks = []
            overlay_b64 = None
            if frame_b64:
                frame = CameraService.decode_base64_frame(frame_b64)
                if frame is not None:
                    frame = CameraService.preprocess_frame(frame)
                    detections = ctx.detector.detect(frame)
                    active_tracks = ctx.tracker.update(detections, presence_threshold=settings.PRESENCE_THRESHOLD_SECONDS)
                    overlay_b64 = CameraService.render_overlay(frame, active_tracks)

            # 3. Multimodal Fusion
            fused = MultimodalFusion.fuse(active_tracks, ctx.last_audio_data)

            # 4. Engagement Engine
            engagement_res = ctx.engagement_engine.calculate_score(fused)
            trend_res = ctx.engagement_engine.get_recent_trend()

            # 5. Rule-based recommendations & LLM pedagogical insights
            ai_output = ctx.ai_service.process_frame_suggestions(fused, engagement_res, trend_res)

            # Persist metrics periodically to database
            now = datetime.utcnow()
            for t in active_tracks:
                pm = PersonMetricModel(
                    session_id=session_id,
                    person_id=f"person_{t['track_id']}",
                    timestamp=now,
                    attention=t["attention_score"],
                    engagement_label=t["engagement_label"],
                    movement=t["movement_score"]
                )
                db.add(pm)

                # Update or register person in DB
                p_db = db.query(PersonModel).filter(
                    PersonModel.id == f"person_{t['track_id']}",
                    PersonModel.session_id == session_id
                ).first()
                if not p_db:
                    p_db = PersonModel(
                        id=f"person_{t['track_id']}",
                        session_id=session_id,
                        label=t["label"],
                        first_seen=now,
                        last_seen=now,
                        presence_seconds=t["presence_seconds"],
                        attendance_status=t["attendance_status"]
                    )
                    db.add(p_db)
                else:
                    p_db.presence_seconds = t["presence_seconds"]
                    p_db.attendance_status = t["attendance_status"]
                    p_db.last_seen = now

            # Persist suggestions triggered
            for s in ai_output.get("suggestions", []):
                sug_model = SuggestionModel(
                    session_id=session_id,
                    timestamp=now,
                    type=s["type"],
                    message=s["message"],
                    rule_id=s["rule_id"]
                )
                db.add(sug_model)

            db.commit()

            # Transmit unified state back to dashboard
            await websocket.send_json({
                "type": "live_sync",
                "timestamp": now.isoformat(),
                "fused": fused,
                "engagement": engagement_res,
                "trend": trend_res,
                "suggestions": ai_output.get("suggestions", []),
                "live_insight": ai_output.get("live_insight", {}),
                "overlay_frame": f"data:image/jpeg;base64,{overlay_b64}" if overlay_b64 else None,
                "active_tracks": active_tracks
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket Live Error] {e}")
    finally:
        db.close()
