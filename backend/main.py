"""
Smart Fence - FastAPI Application Main Entrypoint
Integrates AI Pipeline, REST APIs, WebSockets, and Database Initialization.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, SessionLocal
from backend.models import AlertRecord, DetectionRecord
from backend.routes import (
    detections,
    alerts,
    zones,
    dashboard,
    system,
    video
)
from backend.iot_service import iot_service
from ai.camera import CameraManager
from ai.detection import DetectionEngine
from ai.zones import ZoneManager
from ai.risk_engine import RiskAssessmentEngine
from ai.pipeline import SmartFencePipeline
from ai.config import BACKEND_HOST, BACKEND_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SmartFence.Main")

# Global WebSocket connection manager
active_websockets: Set[WebSocket] = set()


async def broadcast_ws(message: dict):
    """Pushes live events to all connected dashboard browsers."""
    disconnected = set()
    for ws in active_websockets:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.add(ws)
    for dead_ws in disconnected:
        active_websockets.discard(dead_ws)


# Pipeline Event Callbacks
def handle_alert_event(alert_data: dict):
    """Handles alert triggered by AI pipeline: persists to DB & dispatches IoT."""
    logger.info(f"SECURITY ALERT TRIGGERED: {alert_data['risk_level']} - {alert_data['message']}")
    
    # Update dashboard current state
    dashboard.update_current_risk_state(alert_data["risk_level"], alert_data["message"])

    # Persist in SQLite
    db = SessionLocal()
    try:
        alert_record = AlertRecord(
            object_type=alert_data["object_type"],
            tracking_id=alert_data["tracking_id"],
            risk_level=alert_data["risk_level"],
            message=alert_data["message"],
            zone=alert_data["zone"],
            direction=alert_data.get("direction", "UNKNOWN"),
            status="ACTIVE",
            acknowledged=False
        )
        db.add(alert_record)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record alert in DB: {e}")
        db.rollback()
    finally:
        db.close()

    # Dispatch to ESP32 Hardware / Simulator
    iot_service.dispatch_alert(alert_data.get("iot_command", {}))

    # Broadcast via asyncio loop if running
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                broadcast_ws({
                    "type": "ALERT",
                    "data": alert_data
                }),
                loop
            )
    except Exception:
        pass


def handle_detection_event(det_data: dict):
    """Logs detection event to database."""
    db = SessionLocal()
    try:
        det_record = DetectionRecord(
            object_type=det_data["object_type"],
            class_name=det_data["class_name"],
            confidence=det_data["confidence"],
            tracking_id=det_data["track_id"],
            direction=det_data["direction"],
            zone=det_data["zone"],
            risk_level=det_data["risk_level"]
        )
        db.add(det_record)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan: Initializes DB, Camera, YOLO, and Pipeline."""
    logger.info("Initializing Smart Fence System...")
    
    # 1. Initialize SQLite Database
    init_db()
    logger.info("Database schema initialized and seeded.")

    # 2. Initialize Camera and AI Engine
    camera = CameraManager()
    camera_started = camera.start()

    detector = DetectionEngine()
    zone_mgr = ZoneManager()
    risk_eng = RiskAssessmentEngine()

    pipeline = SmartFencePipeline(
        camera=camera,
        detection_engine=detector,
        zone_manager=zone_mgr,
        risk_engine=risk_eng,
        on_alert_callback=handle_alert_event,
        on_detection_callback=handle_detection_event
    )

    # Attach pipeline to video streamer
    video.set_pipeline(pipeline)

    # Update system diagnostics health
    system.set_component_health(
        camera_ok=camera_started,
        ai_ok=detector.is_ready,
        cam_details="Webcam active" if not camera.use_synthetic else "Synthetic Fallback Generator Active",
        ai_details="YOLOv8 ByteTrack Model Loaded" if detector.is_ready else "YOLO Fallback Mode"
    )

    logger.info("Smart Fence AI Pipeline and IoT Services are ONLINE.")
    yield

    # Clean shutdown
    logger.info("Shutting down Smart Fence System...")
    camera.release()
    iot_service.shutdown()


# Initialize FastAPI App
app = FastAPI(
    title="Smart Fence API",
    description="Intelligent Safety & Fence Monitoring System with AI Detection, Tracking, and IoT Alerting",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite development & network clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(detections.router)
app.include_router(alerts.router)
app.include_router(zones.router)
app.include_router(dashboard.router)
app.include_router(system.router)
app.include_router(video.router)


from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/")
    def serve_frontend_root():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/dashboard")
    def serve_frontend_dashboard():
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "system": "Smart Fence Safety Monitoring System",
            "status": "ONLINE",
            "docs_url": "/docs",
            "live_stream_url": "/api/video/feed"
        }


@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """Real-time bidirectional WebSocket stream for dashboard telemetry."""
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        while True:
            # Receive client ping or commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        active_websockets.discard(websocket)
    except Exception:
        active_websockets.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
