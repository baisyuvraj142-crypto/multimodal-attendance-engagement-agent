import os
from typing import Dict, Any, List
from core.config import settings

class LLMInsightGenerator:
    """
    Generates intelligent pedagogical feedback and session summaries.
    Uses Groq API with automatic graceful fallback to deterministic rule-based analysis.
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[LLM] Groq client initialization warning: {e}")
                self.client = None

    def generate_live_insight(self, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates contextual advice for the instructor based on real-time classroom state.
        """
        score = session_context.get("engagement_score", 50.0)
        attendance = session_context.get("students_present", 0)
        audio_state = session_context.get("audio_state", "silence")
        recent_suggestions = session_context.get("recent_suggestions", [])

        # Try Groq API if configured
        if self.client:
            try:
                prompt = (
                    f"You are EduSense AI, an intelligent pedagogical co-pilot for classroom instructors.\n"
                    f"Current Session Status:\n"
                    f"- Current Engagement Score: {score}/100\n"
                    f"- Verified Present Students: {attendance}\n"
                    f"- Room Audio State: {audio_state}\n"
                    f"- Recent alerts: {', '.join([s.get('title', '') for s in recent_suggestions]) or 'None'}\n\n"
                    f"In 2 brief sentences, provide one clear, constructive teaching observation and one concrete tip."
                )
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a concise, helpful classroom teaching co-pilot."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.3
                )
                content = response.choices[0].message.content.strip()
                return {
                    "source": f"Groq LLM ({self.model})",
                    "insight": content
                }
            except Exception as e:
                # Graceful fallback on LLM failure (NFR-4)
                print(f"[LLM] Live insight LLM call failed, falling back to rule-based: {e}")

        # Deterministic rule-based fallback
        return {
            "source": "Rule-based AI Engine",
            "insight": self._generate_rule_based_live_insight(score, audio_state, attendance)
        }

    def generate_session_summary(self, session_data: Dict[str, Any]) -> str:
        """
        Produces end-of-session reflective summary for teacher and students.
        """
        avg_score = session_data.get("avg_engagement", 65.0)
        duration_mins = session_data.get("duration_minutes", 10.0)
        attendance_rate = session_data.get("attendance_rate", 85.0)
        peaks = session_data.get("interaction_peaks", 3)

        if self.client:
            try:
                prompt = (
                    f"Summarize this completed classroom session in 3 constructive sentences.\n"
                    f"- Duration: {duration_mins:.1f} minutes\n"
                    f"- Average Engagement: {avg_score:.1f}%\n"
                    f"- Attendance Rate: {attendance_rate:.1f}%\n"
                    f"- High Interaction Peaks: {peaks}\n"
                    f"Keep the tone encouraging, reflective, and non-punitive."
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an educational analytics summarizer."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.4
                )
                return response.choices[0].message.content.strip()
            except Exception:
                pass

        # Rule-based fallback summary
        if avg_score >= 70:
            quality = "exceptionally engaged and active"
            action = "Sustained vocal exchange and consistent visual focus created strong learning momentum."
        elif avg_score >= 50:
            quality = "moderately focused with steady pacing"
            action = "Core lecture content was delivered stably, with opportunities to boost energy through interactive checks."
        else:
            quality = "quieter than usual with attention ebbs"
            action = "Splitting dense explanatory segments into shorter 10-minute micro-topics will help maintain energy."

        return (
            f"The session concluded with an average engagement of {avg_score:.1f}% across {duration_mins:.1f} minutes. "
            f"Overall participation was {quality}. {action}"
        )

    def _generate_rule_based_live_insight(self, score: float, audio_state: str, attendance: int) -> str:
        if score >= 75:
            return f"Students are showing strong visual attention with active dialogue ({audio_state}). Keep this interactive dynamic going."
        elif score >= 50:
            if audio_state == "active speech":
                return "Good verbal participation detected. Ensure you give pause time for questions from more hesitant students."
            else:
                return "Steady classroom concentration observed. Consider throwing in a short question to check comprehension."
        else:
            return "Class energy appears low. An impromptu think-pair-share exercise or whiteboard example will quickly refocus attention."
