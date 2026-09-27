"""
Smart Fence - Dashboard & Real-Time Analytics API Routes
Queries the real SQLite database to compute accurate metrics and chart series.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import DetectionRecord, AlertRecord
from backend.schemas import DashboardStatsResponse, AnalyticsResponse
from backend.iot_service import iot_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Current active state holder (updated by AI pipeline)
current_state = {
    "risk_level": "LOW",
    "risk_reason": "System active - Monitoring fence boundary."
}


def update_current_risk_state(risk: str, reason: str):
    """Updates in-memory system threat level for dashboard polling."""
    current_state["risk_level"] = risk
    current_state["risk_reason"] = reason


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes real-time statistics from active SQLite database."""
    today_start = datetime.combine(date.today(), datetime.min.time())

    total_detections = db.query(func.count(DetectionRecord.id)).scalar() or 0
    human_detections = db.query(func.count(DetectionRecord.id)).filter(DetectionRecord.object_type == "human").scalar() or 0
    animal_detections = db.query(func.count(DetectionRecord.id)).filter(DetectionRecord.object_type == "animal").scalar() or 0
    
    high_risk_alerts = db.query(func.count(AlertRecord.id)).filter(
        AlertRecord.risk_level.in_(["HIGH", "CRITICAL"])
    ).scalar() or 0

    today_alerts = db.query(func.count(AlertRecord.id)).filter(
        AlertRecord.timestamp >= today_start
    ).scalar() or 0

    active_alerts = db.query(func.count(AlertRecord.id)).filter(
        AlertRecord.status == "ACTIVE"
    ).scalar() or 0

    iot_stat = iot_service.get_status()
    esp32_display = f"{iot_stat['status']} ({iot_stat['mode']})"

    return DashboardStatsResponse(
        total_detections=total_detections,
        human_detections=human_detections,
        animal_detections=animal_detections,
        high_risk_alerts=high_risk_alerts,
        today_alerts=today_alerts,
        active_alerts=active_alerts,
        current_system_risk=current_state["risk_level"],
        current_risk_reason=current_state["risk_reason"],
        esp32_status=esp32_display
    )


@router.get("/analytics", response_model=AnalyticsResponse)
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """Aggregates real data for frontend charts."""
    # 1. Risk distribution from AlertRecord
    risk_counts = db.query(AlertRecord.risk_level, func.count(AlertRecord.id)).group_by(AlertRecord.risk_level).all()
    risk_dict = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for r_lvl, count in risk_counts:
        if r_lvl in risk_dict:
            risk_dict[r_lvl] = count

    # 2. Object distribution from DetectionRecord
    obj_counts = db.query(DetectionRecord.object_type, func.count(DetectionRecord.id)).group_by(DetectionRecord.object_type).all()
    obj_dict = {"human": 0, "animal": 0}
    for obj_t, count in obj_counts:
        obj_dict[obj_t] = count

    # 3. Detection trend over the last 6 hours (grouped by hour)
    now = datetime.utcnow()
    hours_trend = []
    for i in range(5, -1, -1):
        h_start = now - timedelta(hours=i+1)
        h_end = now - timedelta(hours=i)
        cnt = db.query(func.count(DetectionRecord.id)).filter(
            DetectionRecord.timestamp >= h_start,
            DetectionRecord.timestamp < h_end
        ).scalar() or 0
        hours_trend.append({
            "hour": h_end.strftime("%H:00"),
            "detections": cnt
        })

    # 4. Alerts by hour
    alerts_trend = []
    for i in range(5, -1, -1):
        h_start = now - timedelta(hours=i+1)
        h_end = now - timedelta(hours=i)
        cnt = db.query(func.count(AlertRecord.id)).filter(
            AlertRecord.timestamp >= h_start,
            AlertRecord.timestamp < h_end
        ).scalar() or 0
        alerts_trend.append({
            "hour": h_end.strftime("%H:00"),
            "alerts": cnt
        })

    return AnalyticsResponse(
        risk_distribution=risk_dict,
        object_distribution=obj_dict,
        alerts_by_hour=alerts_trend,
        detection_trend=hours_trend
    )
