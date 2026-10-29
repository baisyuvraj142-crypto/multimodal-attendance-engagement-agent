import base64
import cv2
import numpy as np
from typing import Optional, Tuple

class CameraService:
    """
    Handles frame decoding, image preprocessing (low-light enhancement),
    and drawing analytical overlays for visualization.
    """
    @staticmethod
    def decode_base64_frame(data_url_or_base64: str) -> Optional[np.ndarray]:
        try:
            if "," in data_url_or_base64:
                # Strip data:image/jpeg;base64,
                base64_data = data_url_or_base64.split(",", 1)[1]
            else:
                base64_data = data_url_or_base64

            img_bytes = base64.b64decode(base64_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return frame
        except Exception:
            return None

    @staticmethod
    def preprocess_frame(frame: np.ndarray, max_width: int = 640) -> np.ndarray:
        """
        Downsamples high-res frames to maintain >= 10 FPS and applies low-light correction.
        """
        if frame is None:
            return None
        
        h, w = frame.shape[:2]
        if w > max_width:
            scaling = max_width / float(w)
            frame = cv2.resize(frame, (max_width, int(h * scaling)), interpolation=cv2.INTER_AREA)

        # Check average luminance for low-light edge case (FR-6.4)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        if mean_brightness < 60: # Low light condition
            # Apply gamma correction to lift shadows
            inv_gamma = 1.0 / 1.5
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            frame = cv2.LUT(frame, table)

        return frame

    @staticmethod
    def render_overlay(frame: np.ndarray, tracks: list) -> str:
        """
        Draws bounding boxes, IDs, and engagement status on frame and returns base64.
        """
        vis_frame = frame.copy()
        for t in tracks:
            box = t.get("box", [0, 0, 0, 0])
            x, y, w, h = box
            label = t.get("label", "Student")
            status = t.get("attendance_status", "Absent")
            engagement = t.get("engagement_label", "neutral")
            
            # Color code by engagement
            color = (0, 220, 100) if engagement == "focused" else (
                (0, 200, 255) if engagement == "neutral" else (60, 60, 255)
            )

            cv2.rectangle(vis_frame, (x, y), (x + w, y + h), color, 2)
            header_text = f"{label} | {engagement.upper()}"
            sub_text = f"{status} ({t.get('presence_seconds', 0)}s)"
            
            # Label background banner
            cv2.rectangle(vis_frame, (x, y - 36), (x + max(180, w), y), (20, 20, 20), -1)
            cv2.putText(vis_frame, header_text, (x + 4, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
            cv2.putText(vis_frame, sub_text, (x + 4, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1, cv2.LINE_AA)

        _, buffer = cv2.imencode('.jpg', vis_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        return base64.b64encode(buffer).decode('utf-8')
