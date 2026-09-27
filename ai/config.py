"""
Smart Fence - Centralized Configuration System
Loads configuration from environment variables (.env) with safe fallbacks.
Single source of truth for thresholds, zones, classes, and IoT settings.
"""

import os
from typing import List, Tuple, Dict
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# ==============================================================================
# Camera & Video Configuration
# ==============================================================================
# CAMERA_INDEX can be an int (e.g. 0 for webcam) or a string path to video/stream
_cam_env = os.getenv("CAMERA_INDEX", "0")
try:
    CAMERA_INDEX: int | str = int(_cam_env)
except ValueError:
    CAMERA_INDEX = _cam_env

FRAME_WIDTH: int = int(os.getenv("FRAME_WIDTH", "640"))
FRAME_HEIGHT: int = int(os.getenv("FRAME_HEIGHT", "480"))
SIMULATED_FENCE_Y: int = int(os.getenv("SIMULATED_FENCE_Y", "420"))

# ==============================================================================
# AI & Detection Configuration
# ==============================================================================
YOLO_MODEL_PATH: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.50"))
TRACKER_TYPE: str = os.getenv("TRACKER_TYPE", "bytetrack.yaml")

# Class categorization (COCO 80 class subsets)
HUMAN_CLASSES: List[str] = ["person"]
ANIMAL_CLASSES: List[str] = [
    "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe"
]
TARGET_CLASSES: List[str] = HUMAN_CLASSES + ANIMAL_CLASSES

# ==============================================================================
# Tracking & Movement Configuration
# ==============================================================================
MAX_TRACK_HISTORY: int = 30  # Number of centroid positions kept per track
MIN_MOVEMENT_PIXELS: float = 12.0  # Pixel threshold to distinguish movement from stationary noise
FENCE_APPROACH_AXIS: str = "Y"  # Y axis (moving down in frame = approaching fence at bottom)

# Direction constants
DIR_TOWARDS_FENCE: str = "TOWARDS_FENCE"
DIR_AWAY_FROM_FENCE: str = "AWAY_FROM_FENCE"
DIR_STATIONARY: str = "STATIONARY"
DIR_UNKNOWN: str = "UNKNOWN"

# ==============================================================================
# Virtual Fence Zone Configuration (Default 640x480 resolution)
# Points represent (x, y) coordinates of polygon vertices.
# ==============================================================================
ZONE_SAFE: str = "SAFE"
ZONE_WARNING: str = "WARNING"
ZONE_DANGER: str = "DANGER"

DEFAULT_ZONES: Dict[str, List[Tuple[int, int]]] = {
    ZONE_SAFE: [
        (0, 0),
        (FRAME_WIDTH, 0),
        (FRAME_WIDTH, int(FRAME_HEIGHT * 0.50)),
        (0, int(FRAME_HEIGHT * 0.50))
    ],
    ZONE_WARNING: [
        (0, int(FRAME_HEIGHT * 0.50)),
        (FRAME_WIDTH, int(FRAME_HEIGHT * 0.50)),
        (FRAME_WIDTH, int(FRAME_HEIGHT * 0.75)),
        (0, int(FRAME_HEIGHT * 0.75))
    ],
    ZONE_DANGER: [
        (0, int(FRAME_HEIGHT * 0.75)),
        (FRAME_WIDTH, int(FRAME_HEIGHT * 0.75)),
        (FRAME_WIDTH, FRAME_HEIGHT),
        (0, FRAME_HEIGHT)
    ]
}

# Zone display colors in BGR (OpenCV format)
ZONE_COLORS_BGR = {
    ZONE_SAFE: (0, 200, 0),       # Green
    ZONE_WARNING: (0, 215, 255),   # Yellow/Amber
    ZONE_DANGER: (0, 0, 240)       # Red
}

# ==============================================================================
# Risk Assessment & Debouncing Configuration
# ==============================================================================
RISK_LOW: str = "LOW"
RISK_MEDIUM: str = "MEDIUM"
RISK_HIGH: str = "HIGH"
RISK_CRITICAL: str = "CRITICAL"

ALERT_COOLDOWN_SECONDS: float = float(os.getenv("ALERT_COOLDOWN_SECONDS", "5.0"))
CRITICAL_DWELL_SECONDS: float = float(os.getenv("CRITICAL_DWELL_SECONDS", "3.0"))

RISK_COLORS_BGR = {
    RISK_LOW: (0, 200, 0),         # Green
    RISK_MEDIUM: (0, 215, 255),     # Yellow
    RISK_HIGH: (0, 140, 255),       # Orange
    RISK_CRITICAL: (0, 0, 240)      # Red
}

# ==============================================================================
# IoT & Hardware Settings
# ==============================================================================
ESP32_IP: str = os.getenv("ESP32_IP", "192.168.1.150")
ESP32_PORT: int = int(os.getenv("ESP32_PORT", "80"))
ESP32_TIMEOUT_SECONDS: float = float(os.getenv("ESP32_TIMEOUT_SECONDS", "2.0"))
USE_VIRTUAL_ESP32: bool = os.getenv("USE_VIRTUAL_ESP32", "true").lower() in ("true", "1", "yes")

# MQTT Settings
MQTT_BROKER: str = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC: str = os.getenv("MQTT_TOPIC", "smartfence/alerts")

# ==============================================================================
# Backend & Persistence Settings
# ==============================================================================
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/smart_fence.db")
BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
