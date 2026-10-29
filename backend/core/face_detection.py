import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

class FaceDetector:
    """
    Face detection using OpenCV Haar Cascades with optional MediaPipe / DNN fallback.
    Returns structured face detections with bounding boxes, confidence, and attention proxies.
    """
    def __init__(self):
        self.cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        
        # Optional eye cascade for attention estimation
        self.eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        try:
            self.eye_cascade = cv2.CascadeClassifier(self.eye_cascade_path)
        except Exception:
            self.eye_cascade = None

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects faces in a BGR frame.
        Returns a list of dicts:
        [{
            "box": [x, y, w, h],
            "confidence": float,
            "attention_score": float (0-100),
            "eyes_detected": int
        }]
        """
        if frame is None or frame.size == 0:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Equalize histogram to handle low light condition (Edge case FR-6.4)
        gray_eq = cv2.equalizeHist(gray)

        # Multi-scale face detection
        faces = self.face_cascade.detectMultiScale(
            gray_eq,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        detections = []
        for (x, y, w, h) in faces:
            roi_gray = gray_eq[y:y+h, x:x+w]
            
            # Confidence estimation proxy based on bounding box solidity and size
            confidence = min(0.98, max(0.65, 0.70 + (w * h) / (frame.shape[0] * frame.shape[1] * 2)))
            
            # Estimate attention/gaze proxy
            eyes_count = 0
            attention_score = 65.0 # baseline when face is facing front
            if self.eye_cascade is not None and roi_gray.size > 0:
                eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=3, minSize=(10, 10))
                eyes_count = len(eyes)
                if eyes_count >= 2:
                    attention_score = 90.0 # Both eyes visible -> looking forward
                elif eyes_count == 1:
                    attention_score = 75.0 # Partial gaze
                else:
                    attention_score = 55.0 # Head tilted or eyes obscured

            # Penalize extreme aspect ratio distortion (profile tilt)
            aspect_ratio = float(w) / float(h)
            if 0.75 <= aspect_ratio <= 1.25:
                attention_score = min(100.0, attention_score + 10.0)
            else:
                attention_score = max(30.0, attention_score - 15.0)

            detections.append({
                "box": [int(x), int(y), int(w), int(h)],
                "confidence": float(round(confidence, 2)),
                "attention_score": float(round(attention_score, 1)),
                "eyes_detected": eyes_count
            })

        return detections
