from datetime import datetime
from typing import List, Dict, Any
from core.config import settings

class MultimodalFusion:
    """
    Fuses vision signals (presence, attention, movement) and audio signals
    (noise dB, speech activity) aligned by timestamp.
    """
    @staticmethod
    def fuse(visual_tracks: List[Dict[str, Any]], audio_data: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = datetime.utcnow()
        num_students = len(visual_tracks)
        
        if num_students > 0:
            avg_attention = sum(t["attention_score"] for t in visual_tracks) / num_students
            avg_movement = sum(t["movement_score"] for t in visual_tracks) / num_students
            present_count = sum(1 for t in visual_tracks if t.get("attendance_status") == "Present")
            partial_count = sum(1 for t in visual_tracks if t.get("attendance_status") == "Partial")
        else:
            avg_attention = 0.0
            avg_movement = 0.0
            present_count = 0
            partial_count = 0

        noise_db = audio_data.get("noise_db", -50.0)
        speech_ratio = audio_data.get("speech_ratio", 0.0)
        audio_state = audio_data.get("state", "silence")

        return {
            "timestamp": timestamp.isoformat(),
            "students_tracked": num_students,
            "students_present": present_count,
            "students_partial": partial_count,
            "avg_visual_attention": round(avg_attention, 1),
            "avg_movement": round(avg_movement, 1),
            "audio_noise_db": noise_db,
            "audio_speech_ratio": speech_ratio,
            "audio_state": audio_state,
            "participants": visual_tracks
        }
