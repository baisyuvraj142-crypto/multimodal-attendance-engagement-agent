import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import numpy as np
import time
from core.tracking import MultiObjectTracker
from core.engagement import EngagementEngine
from core.recommendations_engine import RecommendationsEngine
from core.audio_analysis import AudioAnalyzer
from core.fusion import MultimodalFusion
from core.analytics_service import AnalyticsService
from core.database import SessionModel, PersonModel, Base, engine, SessionLocal

class TestEduSenseCore(unittest.TestCase):
    def test_acceptance_criteria_1_presence_duration(self):
        """
        Acceptance Criteria 1:
        Attendance is marked 'Present' only when cumulative presence exceeds threshold (e.g. 5.0s here).
        """
        tracker = MultiObjectTracker(max_age=10, min_hits=1, iou_threshold=0.2)
        threshold = 5.0
        
        dets = [{"box": [100, 100, 80, 80], "attention_score": 85.0, "confidence": 0.9}]
        tracks = tracker.update(dets, presence_threshold=threshold)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["attendance_status"], "Absent")

        track = tracker.tracks[0]
        track.presence_seconds = 3.0
        tracks = tracker.update(dets, presence_threshold=threshold)
        self.assertEqual(tracks[0]["attendance_status"], "Partial")

        track.presence_seconds = 5.5
        tracks = tracker.update(dets, presence_threshold=threshold)
        self.assertEqual(tracks[0]["attendance_status"], "Present")
        print(" [PASS] Criteria 1: Presence-based attendance confirmed.")

    def test_acceptance_criteria_2_multimodal_timeline(self):
        """
        Acceptance Criteria 2:
        Engagement timeline renders with both vision and audio contributing.
        """
        eng_engine = EngagementEngine()
        fused_high = {
            "timestamp": "2026-10-29T12:00:00",
            "students_tracked": 3,
            "avg_visual_attention": 90.0,
            "avg_movement": 30.0,
            "audio_state": "active speech",
            "audio_noise_db": -22.0,
            "audio_speech_ratio": 0.6
        }
        score_high = eng_engine.calculate_score(fused_high)
        self.assertGreater(score_high["overall_score"], 75.0)
        self.assertEqual(score_high["level"], "High")
        self.assertIn("visual attention", score_high["explanation"].lower())
        self.assertIn("audio context", score_high["explanation"].lower())
        print(" [PASS] Criteria 2: Multimodal fusion engagement timeline confirmed.")

    def test_acceptance_criteria_3_recommendation_types(self):
        """
        Acceptance Criteria 3:
        At least three distinct teaching suggestion types are generated from test data.
        """
        recs = RecommendationsEngine()
        recs.cooldown_seconds = 0.0

        fused_disengaged = {"students_tracked": 2, "audio_state": "silence", "audio_noise_db": -50.0}
        engagement_low = {"overall_score": 30.0}
        suggestions_1 = recs.evaluate(fused_disengaged, engagement_low, {"delta": 0.0, "is_drop": False})
        types_found = {s["type"] for s in suggestions_1}

        engagement_mid = {"overall_score": 45.0}
        suggestions_2 = recs.evaluate(fused_disengaged, engagement_mid, {"delta": -25.0, "is_drop": True})
        types_found.update({s["type"] for s in suggestions_2})

        fused_active = {"students_tracked": 2, "audio_state": "active speech", "audio_noise_db": -20.0}
        engagement_high = {"overall_score": 88.0}
        suggestions_3 = recs.evaluate(fused_active, engagement_high, {"delta": 5.0, "is_drop": False})
        types_found.update({s["type"] for s in suggestions_3})

        self.assertTrue({"alert", "warning", "info"}.issubset(types_found))
        print(" [PASS] Criteria 3: Distinct suggestion types (alert, warning, info) verified.")

    def test_acceptance_criteria_4_student_summary_no_grades(self):
        """
        Acceptance Criteria 4:
        Student summary contains no grades or rankings.
        """
        db = SessionLocal()
        try:
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
            self.assertEqual(len(summaries), 2)
            for item in summaries:
                self.assertNotIn("grade", item)
                self.assertNotIn("rank", item)
                self.assertNotIn("score", item)
                self.assertIn("reflective_summary", item)
                self.assertIn("attendance_status", item)
            print(" [PASS] Criteria 4: Student summaries strictly ethical and non-punitive.")
        finally:
            db.close()

    def test_acceptance_criteria_5_exports(self):
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

            csv_str = AnalyticsService.export_csv(db, s_id)
            self.assertIn("Participant ID", csv_str)
            self.assertIn("Student_01", csv_str)

            pdf_bytes = AnalyticsService.export_pdf(db, s_id)
            self.assertGreater(len(pdf_bytes), 500)
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))
            print(" [PASS] Criteria 5: PDF and CSV generation verified.")
        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()
