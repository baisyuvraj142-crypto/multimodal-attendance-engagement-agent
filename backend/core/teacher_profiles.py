from typing import Dict, Any, List

class TeacherProfileService:
    """
    Manages teacher effectiveness metrics, trends, benchmarks, and strengths.
    """
    @staticmethod
    def get_profile(teacher_id: str = "teacher_1", session_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if session_history is None or len(session_history) == 0:
            # Baseline mock history if new
            historical_sessions = [
                {"date": "2026-10-22", "title": "Intro to Multimodal AI", "engagement": 74.2, "attendance": 92.0},
                {"date": "2026-10-24", "title": "Signal Processing Basics", "engagement": 68.5, "attendance": 88.5},
                {"date": "2026-10-27", "title": "Audio Feature Engineering", "engagement": 81.0, "attendance": 95.0},
            ]
        else:
            historical_sessions = session_history

        avg_historical_engagement = sum(s["engagement"] for s in historical_sessions) / max(1, len(historical_sessions))
        avg_attendance = sum(s["attendance"] for s in historical_sessions) / max(1, len(historical_sessions))

        # Teacher Effectiveness Score (0-100)
        # Derived from engagement consistency, interaction peaks, and attendance retention
        effectiveness_score = min(100.0, round(avg_historical_engagement * 0.7 + avg_attendance * 0.3, 1))

        # Benchmark comparison against department median (e.g. 70.0%)
        dept_benchmark = 68.0
        comparison_delta = round(effectiveness_score - dept_benchmark, 1)

        return {
            "teacher_id": teacher_id,
            "name": "Dr. Sarah Mitchell",
            "department": "School of Computer Science & AI",
            "effectiveness_score": effectiveness_score,
            "department_benchmark": dept_benchmark,
            "comparison_delta": comparison_delta,
            "comparison_summary": f"{'+' if comparison_delta >= 0 else ''}{comparison_delta}% vs departmental average",
            "sessions_conducted": len(historical_sessions),
            "historical_trend": historical_sessions,
            "strengths": [
                "High vocal interaction during conceptual Q&A segments",
                "Strong presence retention across full 60-minute windows",
                "Swift pacing adjustments following automated attention notices"
            ],
            "actionable_tips": [
                "Consider extending pair-programming pauses by 2 minutes for deeper synthesis.",
                "Incorporate a 3-question mid-lecture retrieval quiz during complex derivations."
            ]
        }
