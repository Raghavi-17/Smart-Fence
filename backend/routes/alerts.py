"""
Smart Fence - Alerts API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import AlertRecord
from backend.schemas import AlertCreate, AlertResponse, AlertAcknowledge
from backend.iot_service import iot_service

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.post("", response_model=AlertResponse, status_code=201)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    """Creates a security alert and pushes warning command to IoT hardware."""
    alert = AlertRecord(
        object_type=payload.object_type,
        tracking_id=payload.tracking_id,
        risk_level=payload.risk_level,
        message=payload.message,
        zone=payload.zone,
        direction=payload.direction,
        status="ACTIVE",
        acknowledged=False
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Dispatch to IoT hardware
    iot_cmd = {
        "risk": payload.risk_level,
        "buzzer": payload.risk_level in ("HIGH", "CRITICAL"),
        "led": payload.risk_level in ("MEDIUM", "HIGH", "CRITICAL"),
        "reason": payload.message,
        "track_id": payload.tracking_id
    }
    iot_service.dispatch_alert(iot_cmd)

    return alert


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    risk_level: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Retrieves paginated alerts with optional risk and status filtering."""
    query = db.query(AlertRecord)
    if risk_level:
        query = query.filter(AlertRecord.risk_level == risk_level)
    if status_filter:
        query = query.filter(AlertRecord.status == status_filter)

    return query.order_by(desc(AlertRecord.timestamp)).offset(skip).limit(limit).all()


@router.put("/{alert_id}/ack", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, payload: AlertAcknowledge, db: Session = Depends(get_db)):
    """Operator acknowledges an active alert."""
    alert = db.query(AlertRecord).filter(AlertRecord.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.acknowledged = payload.acknowledged
    alert.status = payload.status
    db.commit()
    db.refresh(alert)
    return alert
