"""Server-Sent Events (SSE) for real-time count updates + image upload endpoint."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .alert_manager import evaluate_count, get_threshold, subscribe_alerts, unsubscribe_alerts
from .schemas import CountEvent, ModelType, SourceType

logger = logging.getLogger("drishti.count")

router = APIRouter(tags=["count"])

# Add project root
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

UPLOAD_DIR = os.path.join(PROJECT_ROOT, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# In-memory latest count (for SSE)
# ---------------------------------------------------------------------------
_latest_count: dict = {"count": 0, "model": "yolo", "timestamp": "", "threshold": 500, "alert_type": None}
_count_subscribers: list[asyncio.Queue] = []


def update_latest_count(count: int, model: str, alert_type: Optional[str] = None):
    global _latest_count
    _latest_count = {
        "count": count,
        "model": model,
        "timestamp": datetime.utcnow().isoformat(),
        "threshold": get_threshold(),
        "alert_type": alert_type,
    }
    # Push to subscribers
    for q in list(_count_subscribers):
        try:
            q.put_nowait(_latest_count)
        except asyncio.QueueFull:
            pass


# ---------------------------------------------------------------------------
# SSE endpoint
# ---------------------------------------------------------------------------

@router.get("/ws/count")
async def sse_count():
    """Server-Sent Events stream for real-time crowd count updates."""
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    _count_subscribers.append(q)

    async def event_generator():
        try:
            # Send current state immediately
            yield f"data: {json.dumps(_latest_count)}\n\n"
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if q in _count_subscribers:
                _count_subscribers.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# SSE endpoint for alerts
# ---------------------------------------------------------------------------

@router.get("/ws/alerts")
async def sse_alerts():
    """Server-Sent Events stream for real-time alert notifications."""
    q = subscribe_alerts()

    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(data, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe_alerts(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Image / Video upload + inference
# ---------------------------------------------------------------------------

_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def _extract_video_frame(video_path: str) -> str:
    """Extract a representative frame from a video and save as JPEG.

    Picks a frame 25% into the video (avoids blank intros).
    Returns the path to the saved JPEG.
    """
    import cv2

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    target_frame = max(1, total_frames // 4)  # 25% in

    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        raise RuntimeError("Failed to read frame from video")

    frame_path = video_path.rsplit(".", 1)[0] + "_frame.jpg"
    cv2.imwrite(frame_path, frame)
    return frame_path


@router.post("/api/count")
async def count_media(
    file: UploadFile = File(...),
    model: str = Form("yolo"),
):
    """Upload an image or video, run inference, return count + density map."""
    import time

    t0 = time.time()

    # Save uploaded file
    ext = Path(file.filename or "img.jpg").suffix.lower()
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = os.path.join(UPLOAD_DIR, fname)

    with open(fpath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size_mb = os.path.getsize(fpath) / (1024 * 1024)
    t1 = time.time()
    logger.info(f"[TIMING] File saved: {file.filename} ({file_size_mb:.1f} MB) in {t1-t0:.2f}s")

    is_video = ext in _VIDEO_EXTS
    inference_path = fpath

    # For videos, extract a frame first
    if is_video:
        try:
            inference_path = _extract_video_frame(fpath)
            t2 = time.time()
            logger.info(f"[TIMING] Frame extracted in {t2-t1:.2f}s → {inference_path}")
        except Exception as e:
            logger.error(f"Video frame extraction failed: {e}")
            raise HTTPException(status_code=400, detail=f"Could not read video: {e}")
    else:
        t2 = t1

    # Run inference on image (or extracted frame)
    try:
        if model == "csrnet":
            from inferenceCRNet import get_prediction as predict
            prediction, density = predict(inference_path)
        else:
            from inferenceYOLO import get_prediction_yolo as predict
            prediction, density = predict(weights="yolo-crowd.pt", source=inference_path)
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    t3 = time.time()
    logger.info(f"[TIMING] Inference done in {t3-t2:.2f}s — count={prediction}")

    count_value = int(prediction) if isinstance(prediction, (int, float)) else 0

    # Evaluate alert
    source_type = "video" if is_video else "image"
    alert = await evaluate_count(
        count_value=count_value,
        model_used=model,
        source_type=source_type,
        file_path=fpath,
    )

    t4 = time.time()
    logger.info(f"[TIMING] Total: {t4-t0:.2f}s (save={t1-t0:.2f}, extract={t2-t1:.2f}, inference={t3-t2:.2f}, alert={t4-t3:.2f})")

    alert_type = alert.get("alert_type") if alert else None
    update_latest_count(count_value, model, alert_type)

    return {
        "count": count_value,
        "model_used": model,
        "source_type": source_type,
        "density_path": density,
        "original_path": f"static/uploads/{fname}",
        "alert": alert,
    }
