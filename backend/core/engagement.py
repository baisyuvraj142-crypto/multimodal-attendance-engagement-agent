from typing import Dict, Any, List
from collections import deque
from core.config import settings

class EngagementEngine:
    """
    Computes 0-100 engagement score using transparent, configurable rule weights.
    Maintains a temporal window to track drops, sustained periods, and trends.
    """
    def __init__(self, history_maxlen: int = 120):
        self.history = deque(maxlen=history_maxlen)

    def calculate_score(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes composite engagement score from fused multimodal inputs.
        """
        visual_att = fused_data.get("avg_visual_attention", 50.0)
        movement = fused_data.get("avg_movement", 20.0)
        audio_state = fused_data.get("audio_state", "silence")
        noise_db = fused_data.get("audio_noise_db", -50.0)
        speech_ratio = fused_data.get("audio_speech_ratio", 0.0)
        students_tracked = fused_data.get("students_tracked", 0)

        # Baseline when no students are detected
        if students_tracked == 0:
            return {
                "overall_score": 0.0,
                "attention_component": 0.0,
                "movement_component": 0.0,
                "audio_component": 0.0,
                "level": "Inactive",
                "explanation": "No participants visible in camera view."
            }

        # 1. Visual Attention Component (0 - 100)
        att_score = visual_att

        # 2. Movement / Restlessness Component (0 - 100)
        # Moderate movement indicates active participation/note-taking (~20-50).
        # Frozen or extreme fidgeting (>70) is penalized.
        if 15.0 <= movement <= 55.0:
            mov_score = 85.0
        elif movement < 15.0:
            mov_score = 65.0 # quiet / still
        else:
            mov_score = max(30.0, 100.0 - movement) # restless

        # 3. Audio Context Component (0 - 100)
        if audio_state == "active speech":
            # Interactive vocal discussion
            aud_score = min(100.0, 75.0 + speech_ratio * 30.0)
        elif audio_state == "background noise":
            # Noisy distractions
            aud_score = max(25.0, 60.0 - abs(noise_db - settings.NOISY_DECIBEL_THRESHOLD) * 1.5)
        else: # silence
            # Silent listening/lecture: aligned with visual attention
            aud_score = 70.0 if visual_att >= 60.0 else 45.0

        # Weighted combination using configurable parameters (FR-4.4)
        w_att = settings.ATTENTION_WEIGHT
        w_mov = settings.MOVEMENT_WEIGHT
        w_aud = settings.AUDIO_WEIGHT
        total_w = w_att + w_mov + w_aud

        composite = (att_score * w_att + mov_score * w_mov + aud_score * w_aud) / total_w
        composite = round(float(composite), 1)

        # Engagement Level classification
        if composite >= settings.HIGH_INTERACTION_THRESHOLD:
            level = "High"
        elif composite >= settings.DISENGAGEMENT_THRESHOLD:
            level = "Medium"
        else:
            level = "Low"

        # Record into temporal history
        entry = {
            "timestamp": fused_data.get("timestamp"),
            "score": composite,
            "visual_att": att_score,
            "mov_score": mov_score,
            "aud_score": aud_score,
            "level": level
        }
        self.history.append(entry)

        # Explainability breakdown (NFR-5)
        explanation = (
            f"Visual attention scored {att_score:.1f} (weight {w_att*100:.0f}%), "
            f"movement stability scored {mov_score:.1f} (weight {w_mov*100:.0f}%), "
            f"audio context ({audio_state}) contributed {aud_score:.1f} (weight {w_aud*100:.0f}%)."
        )

        return {
            "overall_score": composite,
            "attention_component": round(att_score, 1),
            "movement_component": round(mov_score, 1),
            "audio_component": round(aud_score, 1),
            "level": level,
            "explanation": explanation
        }

    def get_recent_trend(self, lookback_entries: int = 6) -> Dict[str, Any]:
        """Calculates short-term rate of change to detect sharp drops or surges."""
        if len(self.history) < 2:
            return {"delta": 0.0, "is_drop": False, "is_surge": False}

        entries = list(self.history)[-lookback_entries:]
        recent_avg = sum(e["score"] for e in entries[-len(entries)//2:]) / max(1, len(entries)//2)
        prior_avg = sum(e["score"] for e in entries[:len(entries)//2]) / max(1, len(entries)//2)
        delta = round(recent_avg - prior_avg, 1)

        return {
            "delta": delta,
            "is_drop": delta <= -20.0,
            "is_surge": delta >= 18.0
        }
