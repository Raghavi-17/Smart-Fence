"""
Smart Fence - SQLAlchemy Database Models
Defines tables for detections, alerts, virtual zones, and system telemetry logs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from backend.database import Base


class DetectionRecord(Base):
    """Stores individual object detection & tracking occurrences."""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    object_type = Column(String(50), nullable=False, index=True)  # "human", "animal"
    class_name = Column(String(50), nullable=False)               # "person", "dog", "cow", etc.
    confidence = Column(Float, nullable=False)
    tracking_id = Column(Integer, nullable=False, index=True)
    direction = Column(String(50), nullable=False)                # "TOWARDS_FENCE", "AWAY_FROM_FENCE", etc.
    zone = Column(String(50), nullable=False, index=True)         # "SAFE", "WARNING", "DANGER"
    risk_level = Column(String(50), nullable=False, index=True)   # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class AlertRecord(Base):
    """Stores generated security alerts with risk classification and status."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    object_type = Column(String(50), nullable=False)
    tracking_id = Column(Integer, nullable=False, index=True)
    risk_level = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    zone = Column(String(50), nullable=False)
    direction = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), default="ACTIVE", index=True)     # "ACTIVE", "ACKNOWLEDGED", "RESOLVED"
    acknowledged = Column(Boolean, default=False)


class ZoneRecord(Base):
    """Stores virtual fence perimeter zone polygon geometries and settings."""
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50), nullable=False)                # "SAFE", "WARNING", "DANGER"
    coordinates = Column(Text, nullable=False)                    # JSON serialized list of [x, y] points
    enabled = Column(Boolean, default=True)


class SystemLog(Base):
    """Audit logs for system components (Camera, AI, Backend, Database, ESP32)."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    component = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
