"""
Smart Fence - Virtual Fence Zones API Routes
"""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ZoneRecord
from backend.schemas import ZoneCreate, ZoneUpdate, ZoneResponse

router = APIRouter(prefix="/api/zones", tags=["Zones"])


@router.get("", response_model=List[ZoneResponse])
def get_zones(db: Session = Depends(get_db)):
    """Fetches all virtual fence zones."""
    zones = db.query(ZoneRecord).all()
    results = []
    for z in zones:
        coords = json.loads(z.coordinates) if z.coordinates else []
        results.append(
            ZoneResponse(
                id=z.id,
                name=z.name,
                zone_type=z.zone_type,
                coordinates=coords,
                enabled=z.enabled
            )
        )
    return results


@router.post("", response_model=ZoneResponse, status_code=201)
def create_or_update_zone(payload: ZoneCreate, db: Session = Depends(get_db)):
    """Creates a new perimeter zone or updates existing zone of same type."""
    existing = db.query(ZoneRecord).filter(ZoneRecord.zone_type == payload.zone_type).first()
    if existing:
        existing.name = payload.name
        existing.coordinates = json.dumps(payload.coordinates)
        existing.enabled = payload.enabled
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        new_zone = ZoneRecord(
            name=payload.name,
            zone_type=payload.zone_type,
            coordinates=json.dumps(payload.coordinates),
            enabled=payload.enabled
        )
        db.add(new_zone)
        db.commit()
        db.refresh(new_zone)
        target = new_zone

    return ZoneResponse(
        id=target.id,
        name=target.name,
        zone_type=target.zone_type,
        coordinates=json.loads(target.coordinates),
        enabled=target.enabled
    )


@router.put("/{zone_id}", response_model=ZoneResponse)
def update_zone(zone_id: int, payload: ZoneUpdate, db: Session = Depends(get_db)):
    """Updates zone coordinates or enable flag."""
    zone = db.query(ZoneRecord).filter(ZoneRecord.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    if payload.name is not None:
        zone.name = payload.name
    if payload.coordinates is not None:
        zone.coordinates = json.dumps(payload.coordinates)
    if payload.enabled is not None:
        zone.enabled = payload.enabled

    db.commit()
    db.refresh(zone)

    return ZoneResponse(
        id=zone.id,
        name=zone.name,
        zone_type=zone.zone_type,
        coordinates=json.loads(zone.coordinates),
        enabled=zone.enabled
    )
