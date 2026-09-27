"""
Smart Fence - Virtual Fence Zones Module
Handles polygonal zone definitions, point-in-polygon spatial testing,
and visual overlay rendering on camera video frames.
"""

from typing import Dict, List, Tuple, Optional
import cv2
import numpy as np
from ai.config import (
    DEFAULT_ZONES,
    ZONE_SAFE,
    ZONE_WARNING,
    ZONE_DANGER,
    ZONE_COLORS_BGR,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    SIMULATED_FENCE_Y
)


class ZoneManager:
    """
    Manages virtual fence perimeter zones (Safe, Warning, Danger)
    and checks object ground positions against zone boundaries.
    """
    def __init__(self, zones: Optional[Dict[str, List[Tuple[int, int]]]] = None):
        self.zones: Dict[str, np.ndarray] = {}
        configured_zones = zones or DEFAULT_ZONES
        for name, points in configured_zones.items():
            self.set_zone(name, points)

    def set_zone(self, name: str, points: List[Tuple[int, int]]):
        """Sets or updates a zone polygon."""
        self.zones[name] = np.array(points, dtype=np.int32)

    def get_zone_points(self, name: str) -> List[Tuple[int, int]]:
        """Returns the polygon vertices for a given zone."""
        if name in self.zones:
            return [tuple(pt) for pt in self.zones[name].tolist()]
        return []

    def get_all_zones(self) -> Dict[str, List[List[int]]]:
        """Returns all configured zones as serializable dictionaries."""
        return {name: pts.tolist() for name, pts in self.zones.items()}

    def point_in_zone(self, point: Tuple[int, int], zone_name: str) -> bool:
        """
        Uses OpenCV pointPolygonTest to test whether (x, y) is inside the zone.
        Returns True if strictly inside or on the edge.
        """
        if zone_name not in self.zones:
            return False
        poly = self.zones[zone_name]
        dist = cv2.pointPolygonTest(poly, (float(point[0]), float(point[1])), measureDist=False)
        return dist >= 0

    def get_zone_for_point(self, point: Tuple[int, int]) -> str:
        """
        Determines which zone a point belongs to.
        Evaluates in order of highest threat: DANGER -> WARNING -> SAFE.
        """
        if self.point_in_zone(point, ZONE_DANGER):
            return ZONE_DANGER
        if self.point_in_zone(point, ZONE_WARNING):
            return ZONE_WARNING
        if self.point_in_zone(point, ZONE_SAFE):
            return ZONE_SAFE
        # Default fallback if slightly outside predefined polygons
        y = point[1]
        if y >= FRAME_HEIGHT * 0.75:
            return ZONE_DANGER
        elif y >= FRAME_HEIGHT * 0.50:
            return ZONE_WARNING
        return ZONE_SAFE

    def get_zone_for_bbox(self, bbox: Tuple[int, int, int, int]) -> str:
        """
        Determines the zone for a detected object bounding box (x1, y1, x2, y2).
        Uses the bottom-center anchor point (x_mid, y2), representing the object's
        ground contact point (feet), which is the standard in perimeter surveillance.
        """
        x1, y1, x2, y2 = bbox
        bottom_center = (int((x1 + x2) / 2), int(y2))
        return self.get_zone_for_point(bottom_center)

    def draw_zones(self, frame: np.ndarray, alpha: float = 0.20, show_labels: bool = True) -> np.ndarray:
        """
        Renders semi-transparent zone polygons, border lines, and labels on the frame.
        """
        overlay = frame.copy()
        h, w = frame.shape[:2]

        for zone_name, poly in self.zones.items():
            color = ZONE_COLORS_BGR.get(zone_name, (200, 200, 200))
            # Fill polygon on overlay
            cv2.fillPoly(overlay, [poly], color)
            # Draw boundary line on main frame
            cv2.polylines(frame, [poly], isClosed=True, color=color, thickness=2, lineType=cv2.LINE_AA)

            if show_labels and len(poly) > 0:
                # Calculate centroid of polygon for label placement
                M = cv2.moments(poly)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                else:
                    cX, cY = poly[0][0], poly[0][1]

                label = f"{zone_name} ZONE"
                cv2.putText(
                    frame,
                    label,
                    (cX - 50, cY),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                    cv2.LINE_AA
                )

        # Apply transparency blend
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Draw the physical electric fence barrier reference line at SIMULATED_FENCE_Y
        fence_y = SIMULATED_FENCE_Y
        cv2.line(frame, (0, fence_y), (w, fence_y), (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(
            frame,
            "[ SIMULATED FENCE BOUNDARY ]",
            (10, fence_y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            1,
            cv2.LINE_AA
        )

        return frame
