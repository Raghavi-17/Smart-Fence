"""
Smart Fence - Camera Module
Provides resilient frame capture from physical webcams, video files,
or an automated synthetic test feed with simulated intruder motion.
"""

import time
import logging
import cv2
import numpy as np
from typing import Optional, Tuple
from ai.config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    SIMULATED_FENCE_Y
)

logger = logging.getLogger("SmartFence.Camera")


class SyntheticFeedGenerator:
    """
    Generates a synthetic camera feed featuring a realistic background,
    a simulated high-voltage electric fence at the bottom, and moving targets
    (e.g., simulated humans / animals) approaching and retreating from the fence.
    Used for automated testing and fallback when no physical webcam is plugged in.
    """
    def __init__(self, width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT):
        self.width = width
        self.height = height
        self.frame_count = 0
        # Simulation target state
        self.target_x = width // 2
        self.target_y = 60
        self.target_vx = 1.5
        self.target_vy = 2.0
        self.is_human = True

    def generate_frame(self) -> np.ndarray:
        self.frame_count += 1
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Draw outdoor lawn / ground background
        # Sky / Far background (top 35%)
        frame[: int(self.height * 0.35), :] = [60, 50, 45]
        # Grass ground (middle to bottom)
        frame[int(self.height * 0.35) :, :] = [30, 70, 35]

        # Draw grid lines for perspective
        for y_line in range(int(self.height * 0.35), self.height, 40):
            cv2.line(frame, (0, y_line), (self.width, y_line), (25, 60, 30), 1)

        # Draw the physical simulated fence structure at the bottom
        fence_y = SIMULATED_FENCE_Y
        # Fence posts
        for post_x in range(30, self.width, 100):
            cv2.rectangle(frame, (post_x - 4, fence_y - 20), (post_x + 4, self.height - 10), (140, 140, 140), -1)
            cv2.circle(frame, (post_x, fence_y - 20), 6, (0, 165, 255), -1)

        # Fence wires
        for wire_offset in [-15, 0, 15, 30]:
            cv2.line(frame, (0, fence_y + wire_offset), (self.width, fence_y + wire_offset), (180, 180, 180), 2)

        # Fence warning signage
        cv2.putText(
            frame,
            "--- SIMULATED ELECTRIC FENCE BOUNDARY ---",
            (self.width // 2 - 200, self.height - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 220, 255),
            1,
            cv2.LINE_AA
        )

        # Update synthetic target motion
        self.target_y += self.target_vy
        self.target_x += self.target_vx

        # Bounce or turnaround near danger zone
        if self.target_y > fence_y - 30:
            self.target_vy = -abs(self.target_vy)  # Move away
        elif self.target_y < 70:
            self.target_vy = abs(self.target_vy)   # Move toward fence

        if self.target_x > self.width - 80 or self.target_x < 80:
            self.target_vx *= -1

        # Draw a synthetic target (person-like silhouette with head, torso, limbs)
        tx, ty = int(self.target_x), int(self.target_y)
        # Head
        cv2.circle(frame, (tx, ty), 14, (220, 200, 180), -1)
        # Torso
        cv2.rectangle(frame, (tx - 12, ty + 14), (tx + 12, ty + 50), (180, 80, 40), -1)
        # Legs
        cv2.line(frame, (tx - 6, ty + 50), (tx - 10, ty + 85), (50, 50, 160), 4)
        cv2.line(frame, (tx + 6, ty + 50), (tx + 10, ty + 85), (50, 50, 160), 4)

        # Synthetic watermark
        cv2.putText(
            frame,
            "MODE: SYNTHETIC TEST FEED (Camera Fallback)",
            (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        return frame


class CameraManager:
    """
    Manages camera lifecycle: opening, frame acquisition, error recovery,
    and graceful release.
    """
    def __init__(self, source: int | str = CAMERA_INDEX, width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT):
        self.source = source
        self.width = width
        self.height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened = False
        self.use_synthetic = False
        self.synthetic_gen: Optional[SyntheticFeedGenerator] = None
        self._last_frame: Optional[np.ndarray] = None
        self._last_frame_time = 0.0

    def start(self) -> bool:
        """Attempts to open physical camera; falls back to synthetic feed if unavailable."""
        logger.info(f"Opening camera source: {self.source}")
        try:
            # On Windows, try cv2.CAP_DSHOW for fast directshow opening if int source
            if isinstance(self.source, int):
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.source)

            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.is_opened = True
                    self.use_synthetic = False
                    logger.info("Physical camera initialized successfully.")
                    return True
                else:
                    logger.warning("Camera opened but failed to read initial frame.")
        except Exception as e:
            logger.warning(f"Error initializing hardware camera: {e}")

        # Fallback to synthetic feed
        logger.info("Falling back to built-in Synthetic Video Feed.")
        self.use_synthetic = True
        self.synthetic_gen = SyntheticFeedGenerator(self.width, self.height)
        self.is_opened = True
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Reads a single frame. Returns (success, frame).
        Automatically handles camera disconnection and reconnect attempts.
        """
        if not self.is_opened:
            if not self.start():
                return False, None

        if self.use_synthetic and self.synthetic_gen:
            # Simulate ~30 FPS delay
            now = time.time()
            elapsed = now - self._last_frame_time
            if elapsed < 0.033:
                time.sleep(0.033 - elapsed)
            self._last_frame_time = time.time()
            frame = self.synthetic_gen.generate_frame()
            self._last_frame = frame
            return True, frame

        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Resize if needed
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                self._last_frame = frame
                self._last_frame_time = time.time()
                return True, frame
            else:
                logger.warning("Failed to grab camera frame. Switching to synthetic fallback.")
                self.use_synthetic = True
                self.synthetic_gen = SyntheticFeedGenerator(self.width, self.height)
                return True, self.synthetic_gen.generate_frame()

        return False, None

    def release(self):
        """Releases the camera hardware resources cleanly."""
        if self.cap is not None:
            try:
                self.cap.release()
                logger.info("Camera released successfully.")
            except Exception as e:
                logger.error(f"Error releasing camera: {e}")
            finally:
                self.cap = None
        self.is_opened = False
