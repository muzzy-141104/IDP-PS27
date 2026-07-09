"""Supabase client helper for DRISHTI backend."""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this file (drishti/backend/)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

_client = None


def get_client():
    """Lazy-initialise and return the Supabase client."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment / .env"
            )
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ---------------------------------------------------------------------------
# count_logs helpers
# ---------------------------------------------------------------------------

def insert_count_log(
    count_value: int,
    model_used: str,
    source_type: str,
    threshold: int,
    file_path: Optional[str] = None,
) -> dict[str, Any]:
    """Insert a row into count_logs and return the inserted row."""
    row = {
        "count_value": count_value,
        "model_used": model_used,
        "source_type": source_type,
        "threshold": threshold,
    }
    if file_path:
        row["file_path"] = file_path
    resp = get_client().table("count_logs").insert(row).execute()
    return resp.data[0] if resp.data else row


def get_recent_counts(limit: int = 50) -> list[dict]:
    resp = (
        get_client()
        .table("count_logs")
        .select("*")
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------------------------
# alerts helpers
# ---------------------------------------------------------------------------

def insert_alert(
    count_log_id: Optional[str],
    alert_type: str,
    threshold_value: int,
    count_value: int,
    sms_dispatch_id: Optional[str] = None,
) -> dict[str, Any]:
    row = {
        "alert_type": alert_type,
        "threshold_value": threshold_value,
        "count_value": count_value,
        "notification_sent": True,
    }
    if count_log_id:
        row["count_log_id"] = count_log_id
    if sms_dispatch_id:
        row["sms_dispatch_id"] = sms_dispatch_id
    resp = get_client().table("alerts").insert(row).execute()
    return resp.data[0] if resp.data else row


def get_alerts(limit: int = 100) -> list[dict]:
    resp = (
        get_client()
        .table("alerts")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


def acknowledge_alert(alert_id: str, acknowledged_by: str = "operator") -> dict:
    resp = (
        get_client()
        .table("alerts")
        .update({"acknowledged": True, "acknowledged_by": acknowledged_by})
        .eq("id", alert_id)
        .execute()
    )
    return resp.data[0] if resp.data else {}


# ---------------------------------------------------------------------------
# analytics_daily helpers
# ---------------------------------------------------------------------------

def upsert_daily_analytics(
    target_date: date,
    total_counts: int,
    avg_count: float,
    max_count: int,
    alert_count: int,
) -> dict:
    row = {
        "date": str(target_date),
        "total_counts": total_counts,
        "avg_count": avg_count,
        "max_count": max_count,
        "alert_count": alert_count,
    }
    resp = (
        get_client()
        .table("analytics_daily")
        .upsert(row, on_conflict="date")
        .execute()
    )
    return resp.data[0] if resp.data else row

# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def upload_to_storage(file_path: str, bucket_name: str = "drishti-media") -> Optional[str]:
    """Uploads a local file to Supabase Storage and returns the public URL."""
    client = get_client()
    file_name = os.path.basename(file_path)
    
    # We prefix with a timestamp to avoid overwriting files with the same name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    destination_path = f"{timestamp}_{file_name}"
    
    try:
        with open(file_path, 'rb') as f:
            # Upload file
            res = client.storage.from_(bucket_name).upload(
                file=f,
                path=destination_path,
                file_options={"content-type": "image/jpeg"} # default to jpeg, Supabase can guess from extension too
            )
        
        # Get public URL
        url = client.storage.from_(bucket_name).get_public_url(destination_path)
        return url
    except Exception as e:
        print(f"Failed to upload {file_path} to Supabase: {e}")
        return None
