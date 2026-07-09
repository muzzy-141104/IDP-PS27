"""Alert management for DRISHTI — threshold evaluation + notifications."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from .schemas import AlertAcknowledge, AlertOut, AlertType, ManualAlertRequest
from . import supabase_client as db
from .notifications import send_sms_alert, send_voice_alert

logger = logging.getLogger("drishti.alerts")

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# ---------------------------------------------------------------------------
# In-memory threshold (overridden via /settings or env)
# ---------------------------------------------------------------------------

ALERT_THRESHOLD: int = int(os.getenv("ALERT_THRESHOLD", "500"))

# SSE subscribers for alert push
_alert_subscribers: list[asyncio.Queue] = []

# Cooldown for notifications (5 minutes)
_last_alert_times = {
    "warning": 0.0,
    "critical": 0.0
}
COOLDOWN_SECONDS = 300


def get_threshold() -> int:
    return ALERT_THRESHOLD


def set_threshold(value: int) -> None:
    global ALERT_THRESHOLD
    ALERT_THRESHOLD = value


def subscribe_alerts() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _alert_subscribers.append(q)
    return q


def unsubscribe_alerts(q: asyncio.Queue) -> None:
    if q in _alert_subscribers:
        _alert_subscribers.remove(q)


async def _broadcast_alert(alert_data: dict) -> None:
    for q in list(_alert_subscribers):
        try:
            await q.put(alert_data)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

async def evaluate_count(
    count_value: int,
    model_used: str,
    source_type: str,
    file_path: Optional[str] = None,
) -> Optional[dict]:
    """Evaluate count against threshold. Returns alert dict if triggered."""
    threshold = ALERT_THRESHOLD

    # Log the count
    try:
        count_log = db.insert_count_log(
            count_value=count_value,
            model_used=model_used,
            source_type=source_type,
            threshold=threshold,
            file_path=file_path,
        )
        count_log_id = count_log.get("id")
    except Exception as e:
        logger.warning(f"Failed to log count to Supabase: {e}")
        count_log_id = None

    if count_value <= threshold:
        return None

    # Determine alert type and handle escalation
    sms_dispatch_id = None
    current_time = time.time()
    
    if count_value > threshold * 1.5:
        alert_type = AlertType.critical
        if current_time - _last_alert_times["critical"] > COOLDOWN_SECONDS:
            msg = f"Critical alert! Crowd count has reached {count_value}, exceeding the critical limit of {int(threshold * 1.5)}."
            sms_dispatch_id = await asyncio.to_thread(send_voice_alert, msg)
            if not sms_dispatch_id:
                sms_dispatch_id = f"CALL-SIM-{uuid.uuid4().hex[:8].upper()}"
            _last_alert_times["critical"] = current_time
            logger.warning(
                f"[VOICE ESCALATION] Crowd count of {count_value} exceeds critical limit "
                f"({threshold * 1.5:.0f}). Dispatched Voice Call. ID: {sms_dispatch_id}"
            )
        else:
            logger.info("Critical threshold exceeded, but voice call is on cooldown.")
            
    elif count_value > threshold:
        alert_type = AlertType.warning
        if current_time - _last_alert_times["warning"] > COOLDOWN_SECONDS:
            msg = f"DRISHTI Warning: Crowd count is {count_value} (Threshold: {threshold}). Check dashboard immediately."
            sms_dispatch_id = await asyncio.to_thread(send_sms_alert, msg)
            if not sms_dispatch_id:
                sms_dispatch_id = f"SMS-SIM-{uuid.uuid4().hex[:8].upper()}"
            _last_alert_times["warning"] = current_time
            logger.warning(
                f"[SMS ESCALATION] Crowd count of {count_value} exceeds warning limit "
                f"({threshold}). Dispatched SMS. ID: {sms_dispatch_id}"
            )
        else:
            logger.info("Warning threshold exceeded, but SMS is on cooldown.")
    else:
        return None

    # Create alert record
    try:
        alert = db.insert_alert(
            count_log_id=count_log_id,
            alert_type=alert_type.value,
            threshold_value=threshold,
            count_value=count_value,
            sms_dispatch_id=sms_dispatch_id,
        )
    except Exception as e:
        logger.warning(f"Failed to insert alert to Supabase: {e}")
        alert = {
            "id": "local",
            "alert_type": alert_type.value,
            "threshold_value": threshold,
            "count_value": count_value,
            "sms_dispatch_id": sms_dispatch_id,
            "created_at": datetime.utcnow().isoformat(),
        }

    # Broadcast to SSE subscribers
    await _broadcast_alert(alert)

    return alert


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

@router.get("")
async def list_alerts(limit: int = 100):
    """Get alert history."""
    try:
        return db.get_alerts(limit=limit)
    except Exception as e:
        logger.error(f"Failed to fetch alerts: {e}")
        return []


@router.post("/send")
async def send_manual_alert(req: ManualAlertRequest):
    """Trigger a manual emergency alert."""
    alert = {
        "alert_type": AlertType.escalated.value,
        "threshold_value": ALERT_THRESHOLD,
        "count_value": req.count_value,
        "notification_sent": True,
        "created_at": datetime.utcnow().isoformat(),
    }
    try:
        alert = db.insert_alert(
            count_log_id=None,
            alert_type=AlertType.escalated.value,
            threshold_value=ALERT_THRESHOLD,
            count_value=req.count_value,
        )
    except Exception as e:
        logger.warning(f"Failed to insert manual alert: {e}")
        alert["id"] = "local"

    await _broadcast_alert(alert)
    return {"status": "alert_sent", "alert": alert}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, body: AlertAcknowledge):
    """Acknowledge an alert."""
    try:
        result = db.acknowledge_alert(alert_id, body.acknowledged_by)
        return {"status": "acknowledged", "alert": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Threshold endpoints (mounted on /api/settings in main)
# ---------------------------------------------------------------------------

settings_router = APIRouter(prefix="/api/settings", tags=["settings"])


@settings_router.get("/threshold")
async def get_threshold_endpoint():
    return {"threshold": ALERT_THRESHOLD}


@settings_router.post("/threshold")
async def set_threshold_endpoint(config: dict):
    value = config.get("threshold", 500)
    set_threshold(int(value))
    return {"threshold": ALERT_THRESHOLD}
