"""
Smart Fence - Detections API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import DetectionRecord
from backend.schemas import DetectionCreate, DetectionResponse

router = APIRouter(prefix="/api/detections", tags=["Detections"])


@router.post("", response_model=DetectionResponse, status_code=201)
def create_detection(payload: DetectionCreate, db: Session = Depends(get_db)):
    """Ingests a new object detection event."""
    detection = DetectionRecord(
        object_type=payload.object_type,
        class_name=payload.class_name,
        confidence=payload.confidence,
        tracking_id=payload.tracking_id,
        direction=payload.direction,
        zone=payload.zone,
        risk_level=payload.risk_level
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


@router.get("", response_model=List[DetectionResponse])
def get_detections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    object_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    zone: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieves paginated historical detection logs with optional filtering."""
    query = db.query(DetectionRecord)
    if object_type:
        query = query.filter(DetectionRecord.object_type == object_type)
    if risk_level:
        query = query.filter(DetectionRecord.risk_level == risk_level)
    if zone:
        query = query.filter(DetectionRecord.zone == zone)

    return query.order_by(desc(DetectionRecord.timestamp)).offset(skip).limit(limit).all()


@router.get("/recent", response_model=List[DetectionResponse])
def get_recent_detections(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Fetches most recent detections for dashboard live feeds."""
    return db.query(DetectionRecord).order_by(desc(DetectionRecord.timestamp)).limit(limit).all()
