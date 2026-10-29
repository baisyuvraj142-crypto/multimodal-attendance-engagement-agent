import os
from dataclasses import dataclass
from typing import List

@dataclass
class Settings:
    PROJECT_NAME: str = "EduSense AI - Multimodal Attendance & Engagement Agent"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./edusense.db")
    
    # Presence & Attendance Thresholds
    PRESENCE_THRESHOLD_SECONDS: float = float(os.getenv("PRESENCE_THRESHOLD_SECONDS", "60.0"))
    
    # LLM Settings (Groq)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # CORS
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Scoring Parameters (Configurable without code changes)
    WINDOW_SECONDS: int = int(os.getenv("WINDOW_SECONDS", "10"))
    ATTENTION_WEIGHT: float = float(os.getenv("ATTENTION_WEIGHT", "0.45"))
    MOVEMENT_WEIGHT: float = float(os.getenv("MOVEMENT_WEIGHT", "0.20"))
    AUDIO_WEIGHT: float = float(os.getenv("AUDIO_WEIGHT", "0.35"))
    
    DISENGAGEMENT_THRESHOLD: float = float(os.getenv("DISENGAGEMENT_THRESHOLD", "38.0"))
    HIGH_INTERACTION_THRESHOLD: float = float(os.getenv("HIGH_INTERACTION_THRESHOLD", "75.0"))
    NOISY_DECIBEL_THRESHOLD: float = float(os.getenv("NOISY_DECIBEL_THRESHOLD", "-18.0"))
    SILENCE_DECIBEL_THRESHOLD: float = float(os.getenv("SILENCE_DECIBEL_THRESHOLD", "-50.0"))

    def get_allowed_origins(self) -> List[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

settings = Settings()
