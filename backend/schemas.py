"""
Smart Fence - Pydantic Request & Response Schemas
Provides strict validation for API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Detection Schemas
# -----------------------------------------------------------------------------
class DetectionCreate(BaseModel):
    object_type: str = Field(..., example="human")
    class_name: str = Field(..., example="person")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.94)
    tracking_id: int = Field(..., example=12)
    direction: str = Field(..., example="TOWARDS_FENCE")
    zone: str = Field(..., example="WARNING")
    risk_level: str = Field(..., example="HIGH")


class DetectionResponse(BaseModel):
    id: int
    object_type: str
    class_name: str
    confidence: float
    tracking_id: int
    direction: str
    zone: str
    risk_level: str
    timestamp: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Alert Schemas
# -----------------------------------------------------------------------------
class AlertCreate(BaseModel):
    object_type: str = Field(..., example="human")
    tracking_id: int = Field(..., example=12)
    risk_level: str = Field(..., example="HIGH")
    message: str = Field(..., example="Human moving toward fence in danger zone")
    zone: str = Field(..., example="DANGER")
    direction: Optional[str] = Field("TOWARDS_FENCE")


class AlertResponse(BaseModel):
    id: int
    object_type: str
    tracking_id: int
    risk_level: str
    message: str
    zone: str
    direction: Optional[str]
    timestamp: datetime
    status: str
    acknowledged: bool

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    acknowledged: bool = True
    status: str = "ACKNOWLEDGED"


# -----------------------------------------------------------------------------
# Zone Schemas
# -----------------------------------------------------------------------------
class ZoneCreate(BaseModel):
    name: str = Field(..., example="North Fence Warning Zone")
    zone_type: str = Field(..., example="WARNING")  # "SAFE", "WARNING", "DANGER"
    coordinates: List[List[int]] = Field(..., example=[[0, 240], [640, 240], [640, 360], [0, 360]])
    enabled: bool = True


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    coordinates: Optional[List[List[int]]] = None
    enabled: Optional[bool] = None


class ZoneResponse(BaseModel):
    id: int
    name: str
    zone_type: str
    coordinates: List[List[int]]
    enabled: bool

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Dashboard & Analytics Schemas
# -----------------------------------------------------------------------------
class DashboardStatsResponse(BaseModel):
    total_detections: int
    human_detections: int
    animal_detections: int
    high_risk_alerts: int
    today_alerts: int
    active_alerts: int
    current_system_risk: str
    current_risk_reason: str
    esp32_status: str


class AnalyticsResponse(BaseModel):
    risk_distribution: Dict[str, int]
    object_distribution: Dict[str, int]
    alerts_by_hour: List[Dict[str, Any]]
    detection_trend: List[Dict[str, Any]]


# -----------------------------------------------------------------------------
# System Status Schemas
# -----------------------------------------------------------------------------
class ComponentStatus(BaseModel):
    name: str
    status: str  # "ONLINE", "OFFLINE", "READY", "ERROR", "CONNECTED", "DISCONNECTED"
    details: Optional[str] = None


class SystemStatusResponse(BaseModel):
    camera: ComponentStatus
    ai_model: ComponentStatus
    backend: ComponentStatus
    database: ComponentStatus
    esp32: ComponentStatus
    timestamp: datetime


# -----------------------------------------------------------------------------
# IoT Hardware Command Schema
# -----------------------------------------------------------------------------
class IoTCommandPayload(BaseModel):
    risk: str = Field(..., example="HIGH")
    buzzer: bool = Field(..., example=True)
    led: bool = Field(..., example=True)
    reason: Optional[str] = None
