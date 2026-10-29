import cv2
import numpy as np
from typing import Optional, Dict

class AppearanceRecognizer:
    """
    Lightweight, privacy-preserving visual feature descriptor for re-identification.
    Computes spatial color and gradient signatures without storing raw facial images.
    """
    def __init__(self):
        self.known_signatures: Dict[str, np.ndarray] = {}

    def extract_feature(self, face_chip: np.ndarray) -> Optional[np.ndarray]:
        if face_chip is None or face_chip.size == 0:
            return None
        
        # Resize to fixed normalized chip
        resized = cv2.resize(face_chip, (64, 64))
        # Color histogram in HSV
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [16], [0, 256])
        
        # Spatial gradients (Sobel)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobelx**2 + sobely**2)
        grad_hist = np.histogram(grad_mag, bins=16, range=(0, 255))[0].astype(np.float32)

        feat = np.concatenate([hist_h.flatten(), hist_s.flatten(), grad_hist.flatten()])
        norm = np.linalg.norm(feat)
        if norm > 0:
            feat = feat / norm
        return feat

    def register(self, person_id: str, feature: np.ndarray):
        if feature is not None:
            self.known_signatures[person_id] = feature

    def match(self, feature: np.ndarray, threshold: float = 0.75) -> Optional[str]:
        if feature is None or not self.known_signatures:
            return None
        
        best_id = None
        best_sim = -1.0
        for pid, known_feat in self.known_signatures.items():
            sim = float(np.dot(feature, known_feat))
            if sim > best_sim:
                best_sim = sim
                best_id = pid
                
        if best_sim >= threshold:
            return best_id
        return None
