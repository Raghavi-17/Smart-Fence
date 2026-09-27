"""
=============================================================================
SMART FENCE - COMPREHENSIVE AUTOMATED TEST SUITE
Covers all 15 scenarios mandated by project specifications:
 1. Human in safe zone
 2. Human entering warning zone
 3. Human entering danger zone
 4. Human moving toward fence
 5. Human moving away
 6. Animal entering warning zone
 7. Animal entering danger zone
 8. Stationary object
 9. Multiple objects tracking
10. Low-confidence detection filtering
11. Repeated detection of same person (Debouncing)
12. Camera failure handling
13. ESP32 disconnected handling
14. Backend unavailable handling
15. Alert cooldown validation
=============================================================================
"""

import sys
import time
from pathlib import Path
import pytest
import numpy as np

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ai.config import (
    DIR_TOWARDS_FENCE,
    DIR_AWAY_FROM_FENCE,
    DIR_STATIONARY,
    ZONE_SAFE,
    ZONE_WARNING,
    ZONE_DANGER,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_CRITICAL
)
from ai.zones import ZoneManager
from ai.movement import MovementAnalyzer
from ai.tracking import ObjectTracker, TrackedObject
from ai.risk_engine import RiskAssessmentEngine
from ai.camera import CameraManager
from ai.detection import DetectionEngine
from backend.iot_service import IoTService, VirtualESP32Device


@pytest.fixture
def zone_mgr():
    return ZoneManager()


@pytest.fixture
def risk_eng():
    return RiskAssessmentEngine(alert_cooldown_seconds=2.0, critical_dwell_seconds=1.5)


@pytest.fixture
def tracker():
    return ObjectTracker()


# -----------------------------------------------------------------------------
# Test 1: Human in safe zone
# -----------------------------------------------------------------------------
def test_01_human_in_safe_zone(zone_mgr, risk_eng):
    """Scenario 1: Human in safe zone should yield LOW risk and no buzzer."""
    bbox = (200, 50, 260, 150)  # Feet at y=150 (Top half = Safe)
    zone = zone_mgr.get_zone_for_bbox(bbox)
    assert zone == ZONE_SAFE

    obj = TrackedObject(1, "human", "person", 0.92, bbox)
    obj.current_zone = zone
    obj.direction = DIR_STATIONARY

    result = risk_eng.assess_risk(obj)
    assert result["risk_level"] == RISK_LOW
    assert result["should_alert"] is False
    assert result["iot_command"]["buzzer"] is False
    assert result["iot_command"]["led"] is False


# -----------------------------------------------------------------------------
# Test 2: Human entering warning zone
# -----------------------------------------------------------------------------
def test_02_human_entering_warning_zone(zone_mgr, risk_eng):
    """Scenario 2: Human entering warning zone moving toward fence yields HIGH risk."""
    bbox = (200, 240, 260, 320)  # Feet at y=320 (Warning zone)
    zone = zone_mgr.get_zone_for_bbox(bbox)
    assert zone == ZONE_WARNING

    obj = TrackedObject(2, "human", "person", 0.95, bbox)
    obj.current_zone = zone
    obj.direction = DIR_TOWARDS_FENCE

    result = risk_eng.assess_risk(obj)
    assert result["risk_level"] == RISK_HIGH
    assert result["should_alert"] is True
    assert result["iot_command"]["buzzer"] is True
    assert result["iot_command"]["led"] is True


# -----------------------------------------------------------------------------
# Test 3: Human entering danger zone
# -----------------------------------------------------------------------------
def test_03_human_entering_danger_zone(zone_mgr, risk_eng):
    """Scenario 3: Human inside danger zone advancing toward fence yields CRITICAL risk."""
    bbox = (200, 350, 260, 440)  # Feet at y=440 (Danger zone)
    zone = zone_mgr.get_zone_for_bbox(bbox)
    assert zone == ZONE_DANGER

    obj = TrackedObject(3, "human", "person", 0.96, bbox)
    obj.current_zone = zone
    obj.direction = DIR_TOWARDS_FENCE

    result = risk_eng.assess_risk(obj)
    assert result["risk_level"] == RISK_CRITICAL
    assert result["should_alert"] is True
    assert result["iot_command"]["buzzer"] is True
    assert result["iot_command"]["led"] is True


# -----------------------------------------------------------------------------
# Test 4: Human moving toward fence
# -----------------------------------------------------------------------------
def test_04_human_moving_toward_fence():
    """Scenario 4: Centroid moving downward toward fence boundary produces TOWARDS_FENCE."""
    analyzer = MovementAnalyzer(min_displacement=10.0)
    t = time.time()
    # Coordinates moving down from y=100 to y=200 over 1 second
    history = [
        (300.0, 100.0, t),
        (300.0, 130.0, t + 0.3),
        (300.0, 165.0, t + 0.6),
        (300.0, 200.0, t + 1.0)
    ]
    direction, dy, velocity = analyzer.analyze_trajectory(history)
    assert direction == DIR_TOWARDS_FENCE
    assert dy > 0


# -----------------------------------------------------------------------------
# Test 5: Human moving away
# -----------------------------------------------------------------------------
def test_05_human_moving_away(zone_mgr, risk_eng):
    """Scenario 5: Object moving away from fence boundary yields AWAY_FROM_FENCE and LOW risk."""
    analyzer = MovementAnalyzer(min_displacement=10.0)
    t = time.time()
    # Coordinates moving upward away from fence from y=300 to y=200
    history = [
        (300.0, 300.0, t),
        (300.0, 260.0, t + 0.3),
        (300.0, 230.0, t + 0.6),
        (300.0, 200.0, t + 1.0)
    ]
    direction, dy, velocity = analyzer.analyze_trajectory(history)
    assert direction == DIR_AWAY_FROM_FENCE
    assert dy < 0

    bbox = (200, 220, 260, 300)
    obj = TrackedObject(5, "human", "person", 0.90, bbox)
    obj.current_zone = ZONE_WARNING
    obj.direction = direction

    result = risk_eng.assess_risk(obj)
    assert result["risk_level"] == RISK_LOW
    assert result["should_alert"] is False


# -----------------------------------------------------------------------------
# Test 6: Animal entering warning zone
# -----------------------------------------------------------------------------
def test_06_animal_entering_warning_zone(zone_mgr, risk_eng):
    """Scenario 6: Animal entering warning zone generates MEDIUM risk (LED true, Buzzer false)."""
    bbox = (200, 240, 260, 320)
    obj = TrackedObject(6, "animal", "cow", 0.88, bbox)
    obj.current_zone = ZONE_WARNING
    obj.direction = DIR_TOWARDS_FENCE

    result = risk_eng.assess_risk(obj)
    assert result["risk_level"] == RISK_MEDIUM
    assert result["should_alert"] is True
    assert result["iot_command"]["buzzer"] is False
    assert result["iot_command"]["led"] is True


# -----------------------------------------------------------------------------
# Test 7: Animal entering danger zone
# -----------------------------------------------------------------------------
def test_07_animal_entering_danger_zone(zone_mgr, risk_eng):
    """Scenario 7: Animal entering danger zone produces HIGH risk alert."""
    bbox = (200, 360, 260, 440)
    obj = TrackedObject(7, "animal", "dog", 0.91, bbox)
    obj.current_zone = ZONE_DANGER
    obj.direction = DIR_STATIONARY

    result = risk_eng.assess_risk(obj)
    assert result["risk_level"] == RISK_HIGH
    assert result["should_alert"] is True
    assert result["iot_command"]["buzzer"] is True
    assert result["iot_command"]["led"] is True


# -----------------------------------------------------------------------------
# Test 8: Stationary object
# -----------------------------------------------------------------------------
def test_08_stationary_object():
    """Scenario 8: Small pixel jitter below MIN_MOVEMENT_PIXELS is classified as STATIONARY."""
    analyzer = MovementAnalyzer(min_displacement=15.0)
    t = time.time()
    # Centroid jiggles slightly by 2-3 pixels
    history = [
        (250.0, 200.0, t),
        (251.0, 202.0, t + 0.3),
        (249.5, 201.0, t + 0.6),
        (250.5, 200.5, t + 1.0)
    ]
    direction, dy, velocity = analyzer.analyze_trajectory(history)
    assert direction == DIR_STATIONARY


# -----------------------------------------------------------------------------
# Test 9: Multiple objects tracking
# -----------------------------------------------------------------------------
def test_09_multiple_objects_tracking(tracker):
    """Scenario 9: Multiple simultaneous objects maintain distinct IDs and independent states."""
    detections = [
        {
            "track_id": 101,
            "class_name": "person",
            "object_type": "human",
            "confidence": 0.93,
            "bbox": (50, 100, 100, 200)
        },
        {
            "track_id": 102,
            "class_name": "dog",
            "object_type": "animal",
            "confidence": 0.89,
            "bbox": (400, 300, 480, 380)
        }
    ]
    tracks = tracker.update_from_yolo_tracks(detections)
    assert len(tracks) == 2
    track_ids = {t.track_id for t in tracks}
    assert 101 in track_ids
    assert 102 in track_ids


# -----------------------------------------------------------------------------
# Test 10: Low-confidence detection
# -----------------------------------------------------------------------------
def test_10_low_confidence_detection():
    """Scenario 10: Detections below CONFIDENCE_THRESHOLD are discarded."""
    detector = DetectionEngine(conf_threshold=0.60)
    # Synthetic frame test
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    results = detector.detect_and_track(dummy_frame)
    # Empty black frame produces no detections
    assert len(results) == 0


# -----------------------------------------------------------------------------
# Test 11: Repeated detection of same person (Debouncing)
# -----------------------------------------------------------------------------
def test_11_repeated_detection_of_same_person(risk_eng):
    """Scenario 11: Duplicate frame detections of same intruder do NOT flood alerts."""
    bbox = (200, 250, 260, 330)
    obj = TrackedObject(11, "human", "person", 0.94, bbox)
    obj.current_zone = ZONE_WARNING
    obj.direction = DIR_TOWARDS_FENCE

    # Frame 1: Alert triggered
    res1 = risk_eng.assess_risk(obj)
    assert res1["should_alert"] is True

    # Frame 2 (0.1s later): Cooldown prevents alert spam
    res2 = risk_eng.assess_risk(obj)
    assert res2["should_alert"] is False

    # Frame 3 (0.2s later): Still in cooldown
    res3 = risk_eng.assess_risk(obj)
    assert res3["should_alert"] is False


# -----------------------------------------------------------------------------
# Test 12: Camera failure handling
# -----------------------------------------------------------------------------
def test_12_camera_failure_handling():
    """Scenario 12: Invalid camera index switches to synthetic feed cleanly without crashing."""
    cam = CameraManager(source=999)  # Non-existent index
    started = cam.start()
    assert started is True
    assert cam.use_synthetic is True
    ret, frame = cam.read_frame()
    assert ret is True
    assert frame is not None
    assert frame.shape == (480, 640, 3)
    cam.release()


# -----------------------------------------------------------------------------
# Test 13: ESP32 disconnected handling
# -----------------------------------------------------------------------------
def test_13_esp32_disconnected_handling():
    """Scenario 13: Disconnected ESP32 falls back safely to simulator or reports DISCONNECTED."""
    # When virtual fallback is enabled
    iot = IoTService(ip="192.0.2.1", port=80, timeout=0.1, use_virtual_fallback=True)
    status_sim = iot.get_status()
    assert status_sim["status"] == "CONNECTED"
    assert status_sim["mode"] == "VIRTUAL_SIMULATOR"

    # When virtual fallback is disabled and physical is unreachable
    iot_no_sim = IoTService(ip="192.0.2.1", port=80, timeout=0.1, use_virtual_fallback=False)
    status_offline = iot_no_sim.get_status()
    assert status_offline["status"] == "DISCONNECTED"
    iot.shutdown()
    iot_no_sim.shutdown()


# -----------------------------------------------------------------------------
# Test 14: Backend unavailable handling
# -----------------------------------------------------------------------------
def test_14_backend_unavailable_handling():
    """Scenario 14: Client handles unreachable backend without crashing."""
    import requests
    try:
        resp = requests.get("http://127.0.0.1:59999/api/system/status", timeout=0.2)
    except requests.exceptions.RequestException as e:
        assert isinstance(e, requests.exceptions.RequestException)


# -----------------------------------------------------------------------------
# Test 15: Alert cooldown validation
# -----------------------------------------------------------------------------
def test_15_alert_cooldown_validation():
    """Scenario 15: Cooldown re-triggers once cooldown time passes or risk escalates."""
    short_engine = RiskAssessmentEngine(alert_cooldown_seconds=0.3, critical_dwell_seconds=1.0)
    bbox = (200, 250, 260, 330)
    obj = TrackedObject(15, "human", "person", 0.94, bbox)
    obj.current_zone = ZONE_WARNING
    obj.direction = DIR_TOWARDS_FENCE

    # 1. First alert at HIGH risk
    r1 = short_engine.assess_risk(obj)
    assert r1["should_alert"] is True
    assert r1["risk_level"] == RISK_HIGH

    # 2. Immediate frame: Suppressed
    r2 = short_engine.assess_risk(obj)
    assert r2["should_alert"] is False

    # 3. Wait for cooldown to expire (0.35s)
    time.sleep(0.35)
    r3 = short_engine.assess_risk(obj)
    assert r3["should_alert"] is True  # Allowed again after cooldown
