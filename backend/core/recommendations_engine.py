import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.config import settings

class RecommendationsEngine:
    """
    Transparent, explainable rule-based recommendation engine for instructors.
    Evaluates temporal patterns and generates actionable advisory prompts.
    """
    def __init__(self):
        self.last_trigger_times: Dict[str, float] = {}
        self.cooldown_seconds = 20.0 # avoid alert fatigue

    def evaluate(self, fused_data: Dict[str, Any], engagement_data: Dict[str, Any], trend_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        suggestions = []
        now = time.time()
        score = engagement_data.get("overall_score", 50.0)
        audio_state = fused_data.get("audio_state", "silence")
        noise_db = fused_data.get("audio_noise_db", -50.0)
        num_students = fused_data.get("students_tracked", 0)

        if num_students == 0:
            return suggestions

        # Rule 1: Sustained Disengagement (Alert)
        if score < settings.DISENGAGEMENT_THRESHOLD:
            rule_id = "RULE_SUSTAINED_DISENGAGEMENT"
            if now - self.last_trigger_times.get(rule_id, 0) > self.cooldown_seconds:
                self.last_trigger_times[rule_id] = now
                suggestions.append({
                    "rule_id": rule_id,
                    "type": "alert",
                    "title": "Low Engagement Stretch",
                    "message": f"Engagement has dropped to {score:.1f}%. Consider breaking the monologue with a quick poll, cold question, or pair-share prompt.",
                    "explanation": f"Score {score:.1f}% below threshold {settings.DISENGAGEMENT_THRESHOLD}%.",
                    "timestamp": datetime.utcnow().isoformat()
                })

        # Rule 2: Sudden Attention Drop (Warning)
        if trend_data.get("is_drop"):
            rule_id = "RULE_ATTENTION_DROP"
            if now - self.last_trigger_times.get(rule_id, 0) > self.cooldown_seconds:
                self.last_trigger_times[rule_id] = now
                delta = trend_data.get("delta", -20.0)
                suggestions.append({
                    "rule_id": rule_id,
                    "type": "warning",
                    "title": "Sudden Attention Drop",
                    "message": f"Attention dropped rapidly ({delta:+.1f} pts). Re-anchor students with a visual aid, real-world case study, or vocal inflection.",
                    "explanation": f"Calculated slope delta of {delta:.1f} over recent window.",
                    "timestamp": datetime.utcnow().isoformat()
                })

        # Rule 3: Noisy Classroom Interval (Warning)
        if audio_state == "background noise" and noise_db >= settings.NOISY_DECIBEL_THRESHOLD:
            rule_id = "RULE_NOISY_INTERVAL"
            if now - self.last_trigger_times.get(rule_id, 0) > self.cooldown_seconds:
                self.last_trigger_times[rule_id] = now
                suggestions.append({
                    "rule_id": rule_id,
                    "type": "warning",
                    "title": "Elevated Background Noise",
                    "message": f"High acoustic noise ({noise_db:.1f} dB) detected. Check microphone isolation or pause for classroom side-talk settling.",
                    "explanation": f"Acoustic reading of {noise_db:.1f} dB exceeded threshold {settings.NOISY_DECIBEL_THRESHOLD} dB.",
                    "timestamp": datetime.utcnow().isoformat()
                })

        # Rule 4: High Collaborative Interaction (Info)
        if score >= settings.HIGH_INTERACTION_THRESHOLD and audio_state == "active speech":
            rule_id = "RULE_HIGH_INTERACTION"
            if now - self.last_trigger_times.get(rule_id, 0) > self.cooldown_seconds:
                self.last_trigger_times[rule_id] = now
                suggestions.append({
                    "rule_id": rule_id,
                    "type": "info",
                    "title": "High Collaboration Peak",
                    "message": "Dynamic student participation observed. Excellent opportunity to synthesize key takeaways and invite summarizing thoughts.",
                    "explanation": f"Combined score {score:.1f}% >= {settings.HIGH_INTERACTION_THRESHOLD}% with active dialogue.",
                    "timestamp": datetime.utcnow().isoformat()
                })

        # Rule 5: Passive Extended Lecture Mode (Info)
        if audio_state == "silence" and score >= 50.0 and fused_data.get("avg_movement", 0) < 15.0:
            rule_id = "RULE_PASSIVE_LECTURE"
            if now - self.last_trigger_times.get(rule_id, 0) > (self.cooldown_seconds * 2):
                self.last_trigger_times[rule_id] = now
                suggestions.append({
                    "rule_id": rule_id,
                    "type": "info",
                    "title": "Passive Lecture Notice",
                    "message": "Class is listening quietly. Incorporate an interactive knowledge check or prompt a student to explain a concept in their own words.",
                    "explanation": "Quiet acoustic environment with low participant physical activity.",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return suggestions
