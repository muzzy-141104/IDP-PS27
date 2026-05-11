"""Pydantic models for DRISHTI API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ModelType(str, Enum):
    yolo = "yolo"
    csrnet = "csrnet"


class SourceType(str, Enum):
    image = "image"
    video = "video"
    webcam = "webcam"


class AlertType(str, Enum):
    warning = "warning"
    critical = "critical"
    escalated = "escalated"


# ---------------------------------------------------------------------------
# Count
# ---------------------------------------------------------------------------

class CountResponse(BaseModel):
    count: int
    model_used: ModelType
    source_type: SourceType
    density_path: Optional[str] = None
    alert: Optional[AlertOut] = None  # populated when threshold breached


class CountLogOut(BaseModel):
    id: UUID
    timestamp: datetime
    count_value: int
    model_used: str
    source_type: str
    threshold: int
    file_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

class AlertOut(BaseModel):
    id: UUID
    count_log_id: Optional[UUID] = None
    alert_type: AlertType
    threshold_value: int
    count_value: int
    notification_sent: bool = False
    sms_dispatch_id: Optional[str] = None
    police_notified: bool = False
    ambulance_notified: bool = False
    fire_notified: bool = False
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    created_at: datetime


class AlertAcknowledge(BaseModel):
    acknowledged_by: str = "operator"


class ManualAlertRequest(BaseModel):
    message: str = "Manual emergency alert triggered"
    count_value: int = 0


# ---------------------------------------------------------------------------
# Settings / Threshold
# ---------------------------------------------------------------------------

class ThresholdConfig(BaseModel):
    threshold: int = Field(500, ge=1, le=10000)


# ---------------------------------------------------------------------------
# SSE Event
# ---------------------------------------------------------------------------

class CountEvent(BaseModel):
    count: int
    model: str
    timestamp: str
    threshold: int
    alert_type: Optional[str] = None


# Fix forward reference
CountResponse.model_rebuild()
