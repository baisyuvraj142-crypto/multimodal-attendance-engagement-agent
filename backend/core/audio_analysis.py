import numpy as np
from typing import Dict, Any, Tuple
import base64

class AudioAnalyzer:
    """
    Analyzes 16 kHz normalized mono audio chunks.
    Computes noise decibels (dB), speech activity, and classifies sound environment.
    """
    def __init__(self, target_sample_rate: int = 16000):
        self.sample_rate = target_sample_rate
        # Calibrated decibel thresholds
        self.silence_threshold_db = -48.0
        self.speech_threshold_db = -28.0
        self.speech_zcr_min = 0.04
        self.speech_zcr_max = 0.40

    def parse_audio_chunk(self, data: Any) -> np.ndarray:
        """
        Converts bytes, bytearray, or base64 strings into float32 normalized [-1.0, 1.0] samples.
        """
        if isinstance(data, str):
            try:
                raw_bytes = base64.b64decode(data)
            except Exception:
                return np.zeros(0, dtype=np.float32)
        elif isinstance(data, (bytes, bytearray)):
            raw_bytes = data
        else:
            return np.zeros(0, dtype=np.float32)

        if len(raw_bytes) == 0:
            return np.zeros(0, dtype=np.float32)

        # Assuming 16-bit PCM (standard browser WebAudio ScriptProcessor or PCM stream)
        # or 32-bit float
        try:
            samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            return samples
        except Exception:
            try:
                samples = np.frombuffer(raw_bytes, dtype=np.float32)
                return samples
            except Exception:
                return np.zeros(0, dtype=np.float32)

    def analyze_window(self, samples: np.ndarray) -> Dict[str, Any]:
        """
        Computes noise level (dB), speech vs silence ratio, and state classification.
        """
        if samples is None or len(samples) == 0:
            return {
                "noise_db": -60.0,
                "speech_ratio": 0.0,
                "state": "silence",
                "rms": 0.0
            }

        # Calculate RMS energy
        rms = float(np.sqrt(np.mean(samples ** 2)))
        # Convert RMS to decibels (clamped to realistic room range [-80dB, 0dB])
        noise_db = 20.0 * np.log10(max(rms, 1e-5))
        noise_db = float(np.clip(noise_db, -80.0, 0.0))

        # Calculate Zero Crossing Rate (ZCR) for speech activity detection (VAD)
        zero_crossings = np.sum(np.abs(np.diff(samples > 0).astype(int)))
        zcr = float(zero_crossings / max(1, len(samples)))

        # Frame-level energy subdivision (e.g., 20ms subframes)
        subframe_size = int(self.sample_rate * 0.02) # 320 samples for 20ms
        active_subframes = 0
        total_subframes = 0

        if len(samples) >= subframe_size:
            for i in range(0, len(samples) - subframe_size + 1, subframe_size):
                sub = samples[i:i + subframe_size]
                sub_rms = np.sqrt(np.mean(sub ** 2))
                sub_db = 20.0 * np.log10(max(sub_rms, 1e-5))
                if sub_db > self.silence_threshold_db + 8.0:
                    active_subframes += 1
                total_subframes += 1

        speech_ratio = float(active_subframes / max(1, total_subframes))

        # Classify state
        if noise_db < self.silence_threshold_db:
            state = "silence"
        elif noise_db >= self.speech_threshold_db and (self.speech_zcr_min <= zcr <= self.speech_zcr_max) and speech_ratio > 0.25:
            state = "active speech"
        else:
            # Ambient or background room sounds
            state = "background noise" if noise_db > self.silence_threshold_db + 10.0 else "silence"

        return {
            "noise_db": round(noise_db, 1),
            "speech_ratio": round(speech_ratio, 2),
            "state": state,
            "rms": round(rms, 4)
        }
