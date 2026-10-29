import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
import numpy as np

def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH
    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    unionArea = float(boxAArea + boxBArea - interArea)
    if unionArea <= 0:
        return 0.0
    return interArea / unionArea

class Track:
    def __init__(self, track_id: int, box: List[int], attention_score: float, confidence: float):
        self.track_id = track_id
        self.label = f"Student_{track_id:02d}"
        self.box = box
        self.attention_score = attention_score
        self.confidence = confidence
        self.time_since_update = 0
        self.hits = 1
        
        now = datetime.utcnow()
        self.first_seen = now
        self.last_seen = now
        self.last_timestamp = time.time()
        
        self.presence_seconds = 0.0
        self.movement_score = 0.0
        self.prev_centroid = (box[0] + box[2] / 2.0, box[1] + box[3] / 2.0)
        self.history = [self.prev_centroid]

    def update(self, box: List[int], attention_score: float, confidence: float):
        now = datetime.utcnow()
        now_ts = time.time()
        dt = max(0.001, min(1.0, now_ts - self.last_timestamp))
        self.last_timestamp = now_ts
        self.last_seen = now
        
        # Accumulate presence duration
        self.presence_seconds += dt
        
        # Calculate movement score based on centroid displacement
        curr_centroid = (box[0] + box[2] / 2.0, box[1] + box[3] / 2.0)
        dx = curr_centroid[0] - self.prev_centroid[0]
        dy = curr_centroid[1] - self.prev_centroid[1]
        dist = (dx**2 + dy**2)**0.5
        # Movement score normalized (0-100)
        instant_movement = min(100.0, dist * 2.5)
        self.movement_score = 0.7 * self.movement_score + 0.3 * instant_movement
        self.prev_centroid = curr_centroid
        
        self.box = box
        # Exponential smoothing on attention score
        self.attention_score = 0.6 * self.attention_score + 0.4 * attention_score
        self.confidence = confidence
        self.time_since_update = 0
        self.hits += 1
        self.history.append(curr_centroid)
        if len(self.history) > 30:
            self.history.pop(0)

    def mark_missed(self):
        self.time_since_update += 1

class MultiObjectTracker:
    """
    Robust multi-object face tracker preserving participant IDs across frames,
    surviving brief occlusion (up to max_age frames) and accumulating presence duration.
    """
    def __init__(self, max_age: int = 30, min_hits: int = 2, iou_threshold: float = 0.25):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: List[Track] = []
        self.next_id = 1
        self.all_seen_tracks: Dict[int, Track] = {}

    def update(self, detections: List[Dict[str, Any]], presence_threshold: float = 60.0) -> List[Dict[str, Any]]:
        """
        Receives current frame detections and returns active tracks with status.
        """
        # If no active tracks, initiate from detections
        if len(self.tracks) == 0:
            for det in detections:
                new_track = Track(self.next_id, det["box"], det["attention_score"], det["confidence"])
                self.tracks.append(new_track)
                self.all_seen_tracks[self.next_id] = new_track
                self.next_id += 1
        else:
            # Build IoU cost matrix
            num_tracks = len(self.tracks)
            num_dets = len(detections)
            iou_matrix = np.zeros((num_tracks, num_dets), dtype=np.float32)

            for t_idx, track in enumerate(self.tracks):
                for d_idx, det in enumerate(detections):
                    iou_matrix[t_idx, d_idx] = compute_iou(track.box, det["box"])

            matched_tracks = set()
            matched_dets = set()

            # Greedy IoU matching
            if num_tracks > 0 and num_dets > 0:
                indices = np.unravel_index(np.argsort(-iou_matrix, axis=None), iou_matrix.shape)
                for t_idx, d_idx in zip(indices[0], indices[1]):
                    if t_idx in matched_tracks or d_idx in matched_dets:
                        continue
                    if iou_matrix[t_idx, d_idx] >= self.iou_threshold:
                        matched_tracks.add(t_idx)
                        matched_dets.add(d_idx)
                        det = detections[d_idx]
                        self.tracks[t_idx].update(det["box"], det["attention_score"], det["confidence"])

            # Handle unmatched tracks
            for t_idx, track in enumerate(self.tracks):
                if t_idx not in matched_tracks:
                    track.mark_missed()

            # Handle unmatched detections (new faces)
            for d_idx, det in enumerate(detections):
                if d_idx not in matched_dets:
                    new_track = Track(self.next_id, det["box"], det["attention_score"], det["confidence"])
                    self.tracks.append(new_track)
                    self.all_seen_tracks[self.next_id] = new_track
                    self.next_id += 1

            # Remove tracks expired beyond max_age
            self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]

        # Format output
        partial_threshold = max(2.0, presence_threshold * 0.3)
        results = []
        for track in self.tracks:
            # Attendance status computation based on cumulative presence
            attendance_status = "Present" if track.presence_seconds >= presence_threshold else (
                "Partial" if track.presence_seconds >= partial_threshold else "Absent"
            )
            
            # Engagement classification per person
            if track.attention_score >= 70.0:
                engagement_label = "focused"
            elif track.attention_score >= 45.0:
                engagement_label = "neutral"
            else:
                engagement_label = "distracted"

            results.append({
                "track_id": track.track_id,
                "label": track.label,
                "box": track.box,
                "attention_score": round(track.attention_score, 1),
                "movement_score": round(track.movement_score, 1),
                "engagement_label": engagement_label,
                "presence_seconds": round(track.presence_seconds, 1),
                "attendance_status": attendance_status,
                "is_active": track.time_since_update == 0,
                "confidence": track.confidence
            })

        return results

    def get_all_records(self, presence_threshold: float = 60.0) -> List[Dict[str, Any]]:
        """Returns all participants seen throughout the session."""
        partial_threshold = max(2.0, presence_threshold * 0.3)
        records = []
        for t_id, track in self.all_seen_tracks.items():
            status = "Present" if track.presence_seconds >= presence_threshold else (
                "Partial" if track.presence_seconds >= partial_threshold else "Absent"
            )
            records.append({
                "person_id": f"person_{track.track_id}",
                "label": track.label,
                "first_seen": track.first_seen.isoformat(),
                "last_seen": track.last_seen.isoformat(),
                "presence_seconds": round(track.presence_seconds, 1),
                "attendance_status": status,
                "attention_avg": round(track.attention_score, 1)
            })
        return records
