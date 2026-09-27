"""
Smart Fence - System Health & Diagnostics Routes
Monitors live operational status of all subsystems: Camera, AI, Backend, DB, ESP32.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database import get_db
from backend.schemas import SystemStatusResponse, ComponentStatus
from backend.iot_service import iot_service

router = APIRouter(prefix="/api/system", tags=["System Diagnostics"])

# Health references populated by backend startup
system_health = {
    "camera_online": True,
    "ai_model_ready": True,
    "ai_details": "YOLOv8 Object Detection & Tracking",
    "camera_details": "Camera feed active"
}


def set_component_health(camera_ok: bool, ai_ok: bool, cam_details: str = "", ai_details: str = ""):
    system_health["camera_online"] = camera_ok
    system_health["ai_model_ready"] = ai_ok
    if cam_details:
        system_health["camera_details"] = cam_details
    if ai_details:
        system_health["ai_details"] = ai_details


@router.get("/status", response_model=SystemStatusResponse)
def get_system_status(db: Session = Depends(get_db)):
    """Queries and returns health diagnostics across the entire stack."""
    # 1. Database check
    try:
        db.execute(text("SELECT 1"))
        db_status = ComponentStatus(name="Database", status="CONNECTED", details="SQLite ORM Active")
    except Exception as e:
        db_status = ComponentStatus(name="Database", status="ERROR", details=str(e))

    # 2. Camera check
    cam_status_str = "ONLINE" if system_health["camera_online"] else "OFFLINE"
    cam_status = ComponentStatus(name="Camera", status=cam_status_str, details=system_health["camera_details"])

    # 3. AI Model check
    ai_status_str = "READY" if system_health["ai_model_ready"] else "ERROR"
    ai_status = ComponentStatus(name="AI Model", status=ai_status_str, details=system_health["ai_details"])

    # 4. Backend check
    backend_status = ComponentStatus(name="Backend", status="ONLINE", details="FastAPI ASGI Server")

    # 5. ESP32 IoT check
    iot_stat = iot_service.get_status()
    esp32_status = ComponentStatus(
        name="ESP32 IoT",
        status=iot_stat["status"],
        details=f"Mode: {iot_stat['mode']} | Risk: {iot_stat['current_risk']} | Buzzer: {iot_stat['buzzer']}"
    )

    return SystemStatusResponse(
        camera=cam_status,
        ai_model=ai_status,
        backend=backend_status,
        database=db_status,
        esp32=esp32_status,
        timestamp=datetime.utcnow()
    )


@router.post("/iot/trigger-test")
def trigger_iot_test():
    """Manual hardware test button for operator dashboard."""
    test_cmd = {
        "risk": "HIGH",
        "buzzer": True,
        "led": True,
        "reason": "Operator Manual Diagnostic Test"
    }
    success = iot_service.dispatch_alert(test_cmd)
    return {"status": "SUCCESS" if success else "FAILED", "command": test_cmd}
