import pytest
import numpy as np
import time
from core.tracking import MultiObjectTracker
from core.engagement import EngagementEngine
from core.recommendations_engine import RecommendationsEngine
from core.audio_analysis import AudioAnalyzer
from core.fusion import MultimodalFusion
from core.analytics_service import AnalyticsService
from core.database import SessionModel, PersonModel, Base, engine, SessionLocal

def test_attendance_presence_logic():
    """
    Acceptance Criteria 1:
    Attendance is marked 'Present' only when cumulative presence exceeds threshold (e.g. 60s).
    Short appearances accumulate intermittently.
    """
    tracker = MultiObjectTracker(max_age=10, min_hits=1, iou_threshold=0.2)
    threshold = 5.0 # test with 5 seconds threshold
    
    # Simulate face detections at frame 0
    dets = [{"box": [100, 100, 80, 80], "attention_score": 85.0, "confidence": 0.9}]
    tracks = tracker.update(dets, presence_threshold=threshold)
    assert len(tracks) == 1
    assert tracks[0]["attendance_status"] == "Absent"

    # Manually simulate accumulated presence
    track = tracker.tracks[0]
    track.presence_seconds = 3.0
    tracks = tracker.update(dets, presence_threshold=threshold)
    assert tracks[0]["attendance_status"] == "Partial"

    # Cross the threshold
    track.presence_seconds = 5.2
    tracks = tracker.update(dets, presence_threshold=threshold)
    assert tracks[0]["attendance_status"] == "Present"

def test_engagement_multimodal_scoring():
    """
    Acceptance Criteria 2:
    Engagement timeline renders with both vision and audio contributing.
    """
    engine = EngagementEngine()

    # Scenario A: High visual attention + active speech
    fused_high = {
        "timestamp": "2026-10-29T12:00:00",
        "students_tracked": 3,
        "avg_visual_attention": 90.0,
        "avg_movement": 30.0,
        "audio_state": "active speech",
        "audio_noise_db": -22.0,
        "audio_speech_ratio": 0.6
    }
    score_high = engine.calculate_score(fused_high)
    assert score_high["overall_score"] > 75.0
    assert score_high["level"] == "High"
    assert "visual attention" in score_high["explanation"].lower()
    assert "audio context" in score_high["explanation"].lower()

    # Scenario B: Low visual attention + silence
    fused_low = {
        "timestamp": "2026-10-29T12:00:10",
        "students_tracked": 3,
        "avg_visual_attention": 25.0,
        "avg_movement": 75.0,
        "audio_state": "silence",
        "audio_noise_db": -55.0,
        "audio_speech_ratio": 0.0
    }
    score_low = engine.calculate_score(fused_low)
    assert score_low["overall_score"] < 45.0
    assert score_low["level"] == "Low"

def test_recommendation_rules_three_distinct_types():
    """
    Acceptance Criteria 3:
    At least three distinct teaching suggestion types are generated from test data.
    """
    recs = RecommendationsEngine()
    recs.cooldown_seconds = 0.0 # disable cooldown for testing

    # 1. Test Sustained Disengagement (type: alert)
    fused_disengaged = {"students_tracked": 2, "audio_state": "silence", "audio_noise_db": -50.0}
    engagement_low = {"overall_score": 30.0}
    suggestions_1 = recs.evaluate(fused_disengaged, engagement_low, {"delta": 0.0, "is_drop": False})
    types_found = {s["type"] for s in suggestions_1}
    assert "alert" in types_found

    # 2. Test Sudden Attention Drop (type: warning)
    engagement_mid = {"overall_score": 45.0}
    suggestions_2 = recs.evaluate(fused_disengaged, engagement_mid, {"delta": -25.0, "is_drop": True})
    types_found.update({s["type"] for s in suggestions_2})
    assert "warning" in types_found

    # 3. Test High Interaction Peak (type: info)
    fused_active = {"students_tracked": 2, "audio_state": "active speech", "audio_noise_db": -20.0}
    engagement_high = {"overall_score": 88.0}
    suggestions_3 = recs.evaluate(fused_active, engagement_high, {"delta": 5.0, "is_drop": False})
    types_found.update({s["type"] for s in suggestions_3})
    assert "info" in types_found

    # Verify at least three distinct suggestion types exist
    assert len(types_found.intersection({"alert", "warning", "info"})) == 3

def test_student_summary_no_grades_or_rankings():
    """
    Acceptance Criteria 4:
    Student summary contains no grades or rankings (ethical / non-punitive constraint NFR-2).
    """
    db = SessionLocal()
    try:
        # Create dummy session
        s_id = "test_s1"
        db.query(PersonModel).filter(PersonModel.session_id == s_id).delete()
        db.query(SessionModel).filter(SessionModel.id == s_id).delete()
        db.commit()

        sess = SessionModel(id=s_id, title="Test Lab")
        p1 = PersonModel(id="p1", session_id=s_id, label="Student_01", presence_seconds=120.0, attendance_status="Present")
        p2 = PersonModel(id="p2", session_id=s_id, label="Student_02", presence_seconds=25.0, attendance_status="Partial")
        db.add_all([sess, p1, p2])
        db.commit()

        summaries = AnalyticsService.get_student_reflective_summaries(db, s_id)
        assert len(summaries) == 2

        for item in summaries:
            # Must not contain punitive grade/rank keywords
            assert "grade" not in item
            assert "rank" not in item
            assert "score" not in item
            assert "mark" not in item
            # Must contain reflective summary and presence
            assert "reflective_summary" in item
            assert "attendance_status" in item
            assert item["presence_seconds"] > 0
    finally:
        db.close()

def test_pdf_and_csv_export():
    """
    Acceptance Criteria 5:
    PDF and CSV exports download and generate correctly.
    """
    db = SessionLocal()
    try:
        s_id = "test_export_sess"
        db.query(PersonModel).filter(PersonModel.session_id == s_id).delete()
        db.query(SessionModel).filter(SessionModel.id == s_id).delete()
        db.commit()

        sess = SessionModel(id=s_id, title="Algorithm Design Lecture")
        p = PersonModel(id="p_exp", session_id=s_id, label="Student_01", presence_seconds=80.0, attendance_status="Present")
        db.add_all([sess, p])
        db.commit()

        # CSV test
        csv_str = AnalyticsService.export_csv(db, s_id)
        assert "Participant ID" in csv_str
        assert "Student_01" in csv_str
        assert "Present" in csv_str

        # PDF test
        pdf_bytes = AnalyticsService.export_pdf(db, s_id)
        assert len(pdf_bytes) > 500 # Valid non-empty PDF binary
        assert pdf_bytes.startswith(b"%PDF")
    finally:
        db.close()
