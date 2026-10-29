import io
import csv
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from core.database import SessionModel, PersonModel, PersonMetricModel, AudioMetricModel, SuggestionModel
from core.teacher_profiles import TeacherProfileService
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class AnalyticsService:
    """
    Computes session analytics, generates reflective student summaries (no grades/ranks),
    and produces downloadable CSV and PDF reports.
    """
    @staticmethod
    def get_session_trends(db: Session, session_id: str) -> Dict[str, Any]:
        session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session_obj:
            return {"session_id": session_id, "timeline": [], "distribution": {"high": 0, "medium": 0, "low": 0}}

        person_metrics = db.query(PersonMetricModel).filter(
            PersonMetricModel.session_id == session_id
        ).order_by(PersonMetricModel.timestamp).all()

        audio_metrics = db.query(AudioMetricModel).filter(
            AudioMetricModel.session_id == session_id
        ).order_by(AudioMetricModel.timestamp).all()

        # Group by timestamp / 10-second buckets
        timeline = []
        high_cnt, med_cnt, low_cnt = 0, 0, 0

        # Combine metrics chronologically
        audio_dict = {a.timestamp.strftime("%Y-%m-%d %H:%M:%S"): a for a in audio_metrics}

        for pm in person_metrics:
            ts_key = pm.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            am = audio_dict.get(ts_key)
            noise_db = am.noise_db if am else -45.0
            aud_state = am.state if am else "silence"

            score = pm.attention
            if score >= 70:
                high_cnt += 1
            elif score >= 40:
                med_cnt += 1
            else:
                low_cnt += 1

            timeline.append({
                "timestamp": ts_key,
                "attention": round(pm.attention, 1),
                "movement": round(pm.movement, 1),
                "noise_db": round(noise_db, 1),
                "audio_state": aud_state,
                "engagement_score": round(score, 1)
            })

        total = max(1, high_cnt + med_cnt + low_cnt)
        distribution = {
            "high_percentage": round((high_cnt / total) * 100, 1),
            "medium_percentage": round((med_cnt / total) * 100, 1),
            "low_percentage": round((low_cnt / total) * 100, 1),
            "total_samples": len(timeline)
        }

        return {
            "session_id": session_id,
            "title": session_obj.title,
            "start_time": session_obj.start_time.isoformat() if session_obj.start_time else "",
            "end_time": session_obj.end_time.isoformat() if session_obj.end_time else "",
            "timeline": timeline,
            "distribution": distribution
        }

    @staticmethod
    def get_student_reflective_summaries(db: Session, session_id: str) -> List[Dict[str, Any]]:
        """
        NFR-2 & Acceptance Criteria 4:
        Produces reflective, constructive student session summaries WITHOUT grades or peer rankings.
        """
        persons = db.query(PersonModel).filter(PersonModel.session_id == session_id).all()
        summaries = []

        for p in persons:
            duration = p.presence_seconds
            status = p.attendance_status

            if status == "Present":
                trend_desc = "Demonstrated consistent presence throughout lecture and collaborative discussions."
                reflection = "Active participation and visual continuity noted. Sustained attention maintained during explanations."
                consistency = "High Consistency"
            elif status == "Partial":
                trend_desc = "Present for key segments of the classroom session."
                reflection = "Good presence observed during parts of the topic. Reviewing the recorded slides will help bridge intermittent absence."
                consistency = "Moderate Consistency"
            else:
                trend_desc = "Minimal or brief presence recorded during this session."
                reflection = "Encouraged to join earlier to engage with the live concept demos and peer Q&A."
                consistency = "Limited Presence"

            summaries.append({
                "person_id": p.id,
                "label": p.label,
                "presence_seconds": round(duration, 1),
                "attendance_status": status,
                "consistency": consistency,
                "activity_trend": trend_desc,
                "reflective_summary": reflection
            })

        return summaries

    @staticmethod
    def export_csv(db: Session, session_id: str) -> str:
        """Exports attendance and participation metrics to CSV format."""
        persons = db.query(PersonModel).filter(PersonModel.session_id == session_id).all()
        session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["EduSense AI - Session Attendance & Participation Report"])
        writer.writerow(["Session ID", session_id])
        writer.writerow(["Session Title", session_obj.title if session_obj else "Unknown"])
        writer.writerow(["Date", session_obj.start_time.strftime("%Y-%m-%d %H:%M:%S") if session_obj else ""])
        writer.writerow([])
        writer.writerow(["Participant ID", "Anonymized Label", "Presence (seconds)", "Attendance Status", "First Seen", "Last Seen"])

        for p in persons:
            writer.writerow([
                p.id,
                p.label,
                round(p.presence_seconds, 1),
                p.attendance_status,
                p.first_seen.strftime("%H:%M:%S") if p.first_seen else "",
                p.last_seen.strftime("%H:%M:%S") if p.last_seen else ""
            ])

        return output.getvalue()

    @staticmethod
    def export_pdf(db: Session, session_id: str) -> bytes:
        """Exports a formatted PDF analytics report using ReportLab."""
        session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        persons = db.query(PersonModel).filter(PersonModel.session_id == session_id).all()
        suggestions = db.query(SuggestionModel).filter(SuggestionModel.session_id == session_id).all()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor("#1e293b"))
        h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor("#334155"))
        normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#475569"))
        bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=10, leading=14, fontName="Helvetica-Bold")

        story = []

        # Header
        story.append(Paragraph("EduSense AI — Classroom Session Intelligence Report", title_style))
        story.append(Spacer(1, 10))
        
        session_title = session_obj.title if session_obj else "Lecture Session"
        start_str = session_obj.start_time.strftime("%Y-%m-%d %H:%M:%S") if session_obj and session_obj.start_time else "N/A"
        story.append(Paragraph(f"<b>Session Title:</b> {session_title} | <b>Date:</b> {start_str} | <b>ID:</b> {session_id}", normal_style))
        story.append(Spacer(1, 15))

        # Attendance Table
        story.append(Paragraph("Attendance & Presence Summary", h2_style))
        story.append(Spacer(1, 8))

        table_data = [["Participant Label", "Presence Duration", "Attendance Status"]]
        for p in persons:
            table_data.append([p.label, f"{p.presence_seconds:.1f}s", p.attendance_status])

        if len(table_data) == 1:
            table_data.append(["No participants recorded", "-", "-"])

        t = Table(table_data, colWidths=[200, 160, 160])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

        # Pedagogical Suggestions Log
        story.append(Paragraph("Pedagogical Insights & Suggestions Triggered", h2_style))
        story.append(Spacer(1, 8))
        if suggestions:
            for s in suggestions[:8]:
                tag = f"[{s.type.upper()}]"
                story.append(Paragraph(f"<b>{tag} {s.rule_id}:</b> {s.message}", normal_style))
                story.append(Spacer(1, 4))
        else:
            story.append(Paragraph("No automated intervention alerts were triggered during this session.", normal_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
