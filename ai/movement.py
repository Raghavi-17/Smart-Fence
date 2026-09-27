"""
Smart Fence - Movement Direction Analysis Module
Analyzes temporal trajectory of tracked objects to determine
whether they are moving toward the fence, away, stationary, or unknown.
Applies temporal smoothing to eliminate single-frame bounding box jitter.
"""

from typing import List, Tuple, Optional
import time
import numpy as np
from ai.config import (
    DIR_TOWARDS_FENCE,
    DIR_AWAY_FROM_FENCE,
    DIR_STATIONARY,
    DIR_UNKNOWN,
    MIN_MOVEMENT_PIXELS
)


class TrackPoint:
    """Represents an object's centroid and timestamp at a single instant."""
    def __init__(self, x: float, y: float, timestamp: Optional[float] = None):
        self.x = x
        self.y = y
        self.timestamp = timestamp or time.time()


class MovementAnalyzer:
    """
    Computes smoothed trajectory vectors and movement direction
    relative to the virtual fence line.
    """
    def __init__(self, min_displacement: float = MIN_MOVEMENT_PIXELS, min_frames: int = 3):
        self.min_displacement = min_displacement
        self.min_frames = min_frames

    def analyze_trajectory(self, history: List[Tuple[float, float, float]]) -> Tuple[str, float, float]:
        """
        Takes a list of (x, y, timestamp) records in chronological order.
        Returns:
            - direction: TOWARDS_FENCE, AWAY_FROM_FENCE, STATIONARY, or UNKNOWN
            - dy_smooth: smoothed delta Y displacement
            - velocity_px_per_sec: velocity magnitude in image space
        """
        if len(history) < self.min_frames:
            return DIR_UNKNOWN, 0.0, 0.0

        # Extract coordinates and times
        ys = np.array([pt[1] for pt in history])
        xs = np.array([pt[0] for pt in history])
        ts = np.array([pt[2] for pt in history])

        dt = ts[-1] - ts[0]
        if dt <= 0:
            dt = 0.001

        # Use recent 5-8 points for responsive short-term trend
        window = min(8, len(history))
        recent_ys = ys[-window:]
        recent_xs = xs[-window:]
        recent_ts = ts[-window:]

        # Linear fit for robust slope estimation (dy/dt) without noise
        time_offsets = recent_ts - recent_ts[0]
        if len(time_offsets) >= 3 and (time_offsets[-1] - time_offsets[0]) > 0.05:
            # Fit polynomial degree 1 (y = m*t + c)
            slope_y, _ = np.polyfit(time_offsets, recent_ys, 1)
            slope_x, _ = np.polyfit(time_offsets, recent_xs, 1)
            net_dy = slope_y * (recent_ts[-1] - recent_ts[0])
            net_dx = slope_x * (recent_ts[-1] - recent_ts[0])
        else:
            net_dy = recent_ys[-1] - recent_ys[0]
            net_dx = recent_xs[-1] - recent_xs[0]

        total_displacement = np.sqrt(net_dx**2 + net_dy**2)
        velocity_px_sec = float(total_displacement / max(0.1, recent_ts[-1] - recent_ts[0]))

        # Check if movement exceeds noise threshold
        if total_displacement < self.min_displacement:
            return DIR_STATIONARY, float(net_dy), velocity_px_sec

        # Since simulated fence is at the bottom (higher Y coordinate in image space):
        # positive net_dy means moving downward towards the fence.
        # negative net_dy means moving upward away from the fence.
        if net_dy > (self.min_displacement * 0.6):
            return DIR_TOWARDS_FENCE, float(net_dy), velocity_px_sec
        elif net_dy < -(self.min_displacement * 0.6):
            return DIR_AWAY_FROM_FENCE, float(net_dy), velocity_px_sec
        else:
            # Primarily lateral movement
            return DIR_STATIONARY, float(net_dy), velocity_px_sec
