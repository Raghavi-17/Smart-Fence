"""
Smart Fence - Object Tracking Module
Maintains track histories, calculates spatial-temporal metrics,
and bridges raw YOLO detections into persistent tracked entities.
"""

import time
from typing import Dict, List, Tuple, Optional
import numpy as np
from ai.config import (
    MAX_TRACK_HISTORY,
    DIR_UNKNOWN,
    ZONE_SAFE,
    RISK_LOW
)
from ai.movement import MovementAnalyzer


class TrackedObject:
    """
    Encapsulates all temporal and spatial state for an active tracked target.
    """
    def __init__(
        self,
        track_id: int,
        object_type: str,
        class_name: str,
        confidence: float,
        bbox: Tuple[int, int, int, int]
    ):
        self.track_id = track_id
        self.object_type = object_type  # "human" or "animal"
        self.class_name = class_name    # "person", "dog", "cow", etc.
        self.confidence = confidence
        self.bbox = bbox                # (x1, y1, x2, y2)

        now = time.time()
        self.first_seen = now
        self.last_seen = now
        self.history: List[Tuple[float, float, float]] = []  # [(x, y, timestamp), ...]
        
        # Bottom-center represents ground position
        cx = (bbox[0] + bbox[2]) / 2.0
        ground_y = float(bbox[3])
        self.history.append((cx, ground_y, now))

        # Dynamic state
        self.direction = DIR_UNKNOWN
        self.current_zone = ZONE_SAFE
        self.risk_level = RISK_LOW
        self.risk_reason = "Initial detection"
        self.velocity = 0.0
        self.net_dy = 0.0
        self.dwell_in_danger_zone = 0.0
        self.danger_zone_entry_time: Optional[float] = None
        self.last_alert_time = 0.0

    @property
    def current_position(self) -> Tuple[float, float]:
        """Returns the most recent (x, y) ground position."""
        if self.history:
            return self.history[-1][0], self.history[-1][1]
        return (self.bbox[0] + self.bbox[2]) / 2.0, float(self.bbox[3])

    @property
    def previous_position(self) -> Tuple[float, float]:
        """Returns the previous (x, y) position before the current one."""
        if len(self.history) >= 2:
            return self.history[-2][0], self.history[-2][1]
        return self.current_position

    def update(
        self,
        bbox: Tuple[int, int, int, int],
        confidence: float,
        movement_analyzer: MovementAnalyzer
    ):
        """Updates the track state with a newly associated detection bounding box."""
        now = time.time()
        self.last_seen = now
        self.bbox = bbox
        self.confidence = confidence

        cx = (bbox[0] + bbox[2]) / 2.0
        ground_y = float(bbox[3])
        self.history.append((cx, ground_y, now))

        if len(self.history) > MAX_TRACK_HISTORY:
            self.history.pop(0)

        # Analyze trajectory
        direction, net_dy, velocity = movement_analyzer.analyze_trajectory(self.history)
        self.direction = direction
        self.net_dy = net_dy
        self.velocity = velocity


class ObjectTracker:
    """
    Manages active tracked objects, matches detections across frames,
    and purges lost tracks.
    """
    def __init__(self, max_missed_seconds: float = 2.0):
        self.tracks: Dict[int, TrackedObject] = {}
        self.next_track_id = 1
        self.max_missed_seconds = max_missed_seconds
        self.movement_analyzer = MovementAnalyzer()

    def update_from_yolo_tracks(
        self,
        detections: List[dict]
    ) -> List[TrackedObject]:
        """
        Accepts YOLO tracked detections containing:
        {
            'track_id': int or None,
            'bbox': (x1, y1, x2, y2),
            'confidence': float,
            'class_name': str,
            'object_type': str
        }
        Updates internal tracks and returns active tracked objects.
        """
        now = time.time()
        current_frame_track_ids = set()

        for det in detections:
            tid = det.get("track_id")
            if tid is None:
                # Assign internal fallback ID if tracker didn't provide one
                tid = self._find_best_match(det["bbox"])
                if tid is None:
                    tid = self.next_track_id
                    self.next_track_id += 1

            current_frame_track_ids.add(tid)

            if tid in self.tracks:
                self.tracks[tid].update(
                    det["bbox"],
                    det["confidence"],
                    self.movement_analyzer
                )
            else:
                self.tracks[tid] = TrackedObject(
                    track_id=tid,
                    object_type=det["object_type"],
                    class_name=det["class_name"],
                    confidence=det["confidence"],
                    bbox=det["bbox"]
                )

        # Clean up stale tracks
        expired = [
            tid for tid, obj in self.tracks.items()
            if (now - obj.last_seen) > self.max_missed_seconds
        ]
        for tid in expired:
            del self.tracks[tid]

        return list(self.tracks.values())

    def _find_best_match(self, bbox: Tuple[int, int, int, int]) -> Optional[int]:
        """Matches unassociated bbox to existing tracks via IoU/distance."""
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        best_id = None
        min_dist = 80.0  # Max pixel distance for same-object continuity

        for tid, obj in self.tracks.items():
            last_cx, last_cy = obj.current_position
            dist = np.sqrt((cx - last_cx)**2 + (cy - last_cy)**2)
            if dist < min_dist:
                min_dist = dist
                best_id = tid

        return best_id
