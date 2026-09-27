"""
Smart Fence - End-to-End AI Pipeline
Coordinates Camera -> Detection -> Tracking -> Zones -> Movement -> Risk Engine
-> Frame Annotation -> Alert/Event Generation.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
import cv2
import numpy as np

from ai.config import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
    RISK_COLORS_BGR,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL
)
from ai.camera import CameraManager
from ai.detection import DetectionEngine
from ai.tracking import ObjectTracker, TrackedObject
from ai.zones import ZoneManager
from ai.risk_engine import RiskAssessmentEngine

logger = logging.getLogger("SmartFence.Pipeline")


class SmartFencePipeline:
    """
    Main pipeline integrating all vision, tracking, and risk intelligence.
    """
    def __init__(
        self,
        camera: Optional[CameraManager] = None,
        detection_engine: Optional[DetectionEngine] = None,
        zone_manager: Optional[ZoneManager] = None,
        risk_engine: Optional[RiskAssessmentEngine] = None,
        on_alert_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_detection_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.camera = camera or CameraManager()
        self.detector = detection_engine or DetectionEngine()
        self.zones = zone_manager or ZoneManager()
        self.tracker = ObjectTracker()
        self.risk_engine = risk_engine or RiskAssessmentEngine()
        
        self.on_alert = on_alert_callback
        self.on_detection = on_detection_callback

        self.last_pipeline_time = time.time()
        self.fps = 0.0
        self.current_max_risk = RISK_LOW
        self.current_risk_reason = "System monitoring active - No threats detected."

    def process_frame(self) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Processes a single frame from the camera through the complete intelligence stack.
        Returns:
            - annotated_frame (np.ndarray): OpenCV BGR frame ready for streaming
            - telemetry (dict): structured frame metadata, active tracks, generated alerts
        """
        t0 = time.time()
        success, frame = self.camera.read_frame()
        if not success or frame is None:
            # Create a blank fallback error frame
            blank = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.putText(
                blank,
                "CAMERA FEED UNAVAILABLE",
                (FRAME_WIDTH // 2 - 160, FRAME_HEIGHT // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )
            return blank, {
                "success": False,
                "error": "Camera frame acquisition failed",
                "tracks": [],
                "max_risk": RISK_LOW
            }

        # 1. Overlay Virtual Fence Zones
        annotated_frame = self.zones.draw_zones(frame.copy(), alpha=0.20, show_labels=True)

        # 2. Run Object Detection & Tracking
        raw_detections = self.detector.detect_and_track(frame)
        active_tracks = self.tracker.update_from_yolo_tracks(raw_detections)

        # 3. Evaluate Zones, Movement, and Risk per Track
        frame_detections_meta = []
        frame_alerts = []
        max_risk = RISK_LOW
        max_risk_reason = "Perimeter safe; no active threats detected."

        severity_map = {RISK_LOW: 0, RISK_MEDIUM: 1, RISK_HIGH: 2, RISK_CRITICAL: 3}

        for obj in active_tracks:
            # Assign current zone
            obj.current_zone = self.zones.get_zone_for_bbox(obj.bbox)

            # Assess multi-factor risk
            risk_result = self.risk_engine.assess_risk(obj)
            risk_level = risk_result["risk_level"]
            reason = risk_result["reason"]

            if severity_map[risk_level] > severity_map[max_risk]:
                max_risk = risk_level
                max_risk_reason = reason

            det_info = {
                "track_id": obj.track_id,
                "class_name": obj.class_name,
                "object_type": obj.object_type,
                "confidence": obj.confidence,
                "bbox": obj.bbox,
                "zone": obj.current_zone,
                "direction": obj.direction,
                "risk_level": risk_level,
                "reason": reason,
                "velocity": round(obj.velocity, 1)
            }
            frame_detections_meta.append(det_info)

            # Fire detection callback
            if self.on_detection:
                try:
                    self.on_detection(det_info)
                except Exception as e:
                    logger.error(f"Error executing on_detection callback: {e}")

            # Check if an alert was triggered
            if risk_result["should_alert"]:
                alert_payload = {
                    "object_type": obj.object_type,
                    "class_name": obj.class_name,
                    "tracking_id": obj.track_id,
                    "risk_level": risk_level,
                    "message": reason,
                    "zone": obj.current_zone,
                    "direction": obj.direction,
                    "confidence": obj.confidence,
                    "iot_command": risk_result["iot_command"],
                    "timestamp": time.time()
                }
                frame_alerts.append(alert_payload)
                if self.on_alert:
                    try:
                        self.on_alert(alert_payload)
                    except Exception as e:
                        logger.error(f"Error executing on_alert callback: {e}")

            # 4. Render Annotations on Frame
            self._render_track_annotation(annotated_frame, obj)

        self.current_max_risk = max_risk
        self.current_risk_reason = max_risk_reason

        # 5. Render HUD Overlay (Status, FPS, Threat Level Banner)
        t_now = time.time()
        dt = t_now - self.last_pipeline_time
        if dt > 0:
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
        self.last_pipeline_time = t_now

        self._render_hud(annotated_frame, max_risk, max_risk_reason, len(active_tracks))

        telemetry = {
            "success": True,
            "fps": round(self.fps, 1),
            "max_risk": max_risk,
            "risk_reason": max_risk_reason,
            "active_tracks_count": len(active_tracks),
            "detections": frame_detections_meta,
            "alerts": frame_alerts
        }

        return annotated_frame, telemetry

    def _render_track_annotation(self, frame: np.ndarray, obj: TrackedObject):
        """Draws bounding box, tracking trail, and status pill for a tracked object."""
        x1, y1, x2, y2 = obj.bbox
        risk_color = RISK_COLORS_BGR.get(obj.risk_level, (0, 255, 0))

        # Draw trajectory history line
        if len(obj.history) > 1:
            points = np.array([(int(pt[0]), int(pt[1])) for pt in obj.history], np.int32)
            cv2.polylines(frame, [points], isClosed=False, color=(255, 255, 255), thickness=1, lineType=cv2.LINE_AA)
            # Dot at current ground position
            cv2.circle(frame, (int(obj.history[-1][0]), int(obj.history[-1][1])), 4, risk_color, -1)

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), risk_color, 2, cv2.LINE_AA)

        # Header tag: "[ID] Class | Conf%"
        tag_text = f"#{obj.track_id} {obj.class_name.upper()} {int(obj.confidence * 100)}%"
        (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        tag_y1 = max(0, y1 - th - 8)
        cv2.rectangle(frame, (x1, tag_y1), (x1 + tw + 8, y1), risk_color, -1)
        cv2.putText(frame, tag_text, (x1 + 4, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        # Bottom info badge: "Zone | Direction | Risk"
        dir_short = {
            "TOWARDS_FENCE": "--> FENCE",
            "AWAY_FROM_FENCE": "<-- AWAY",
            "STATIONARY": "STATIONARY",
            "UNKNOWN": "ANALYZING"
        }.get(obj.direction, obj.direction)

        badge_text = f"{obj.current_zone} | {dir_short} | {obj.risk_level}"
        (bw, bh), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.40, 1)
        b_y1 = min(frame.shape[0] - bh - 6, y2)
        cv2.rectangle(frame, (x1, b_y1), (x1 + bw + 8, b_y1 + bh + 6), (20, 20, 20), -1)
        cv2.rectangle(frame, (x1, b_y1), (x1 + bw + 8, b_y1 + bh + 6), risk_color, 1)
        cv2.putText(frame, badge_text, (x1 + 4, b_y1 + bh + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.40, risk_color, 1, cv2.LINE_AA)

    def _render_hud(self, frame: np.ndarray, max_risk: str, reason: str, count: int):
        """Draws top HUD status banner and active risk level banner."""
        h, w = frame.shape[:2]

        # Top banner background
        cv2.rectangle(frame, (0, 0), (w, 36), (15, 20, 25), -1)
        cv2.line(frame, (0, 36), (w, 36), (40, 50, 60), 1)

        # Title & FPS
        cv2.putText(
            frame,
            "SMART FENCE AI MONITOR",
            (12, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        fps_text = f"FPS: {self.fps:.1f} | ACTIVE TARGETS: {count}"
        cv2.putText(
            frame,
            fps_text,
            (w - 240, 23),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (180, 180, 180),
            1,
            cv2.LINE_AA
        )

        # Risk indicator badge in top right/center
        risk_color = RISK_COLORS_BGR.get(max_risk, (0, 255, 0))
        risk_pill = f"SYSTEM THREAT: {max_risk}"
        (rw, rh), _ = cv2.getTextSize(risk_pill, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 2)
        rx1 = (w // 2) - (rw // 2)
        cv2.rectangle(frame, (rx1 - 8, 5), (rx1 + rw + 8, 31), risk_color, -1)
        cv2.putText(frame, risk_pill, (rx1, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 2, cv2.LINE_AA)
