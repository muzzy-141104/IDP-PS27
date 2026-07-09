"""MJPEG stream router — wraps existing camera_*.py VideoCamera classes."""

from __future__ import annotations

import sys
import os
import logging
from pathlib import Path
from typing import Generator

import cv2
import numpy as np

import asyncio
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger("drishti.stream")

router = APIRouter(tags=["stream"])

# Add project root to sys.path so we can import existing camera modules
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Minimum file size (bytes) to consider a video valid — tiny files can't hold real frames
_MIN_VIDEO_SIZE = 50_000  # 50 KB


def _make_placeholder_jpeg(text: str = "No video source available") -> bytes:
    """Create a 640x360 dark placeholder JPEG with a message."""
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    img[:] = (20, 20, 30)  # match DRISHTI dark theme

    # Draw border
    cv2.rectangle(img, (10, 10), (629, 349), (60, 60, 80), 1)

    # Centre text
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale, thickness = 0.6, 1
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    x = (640 - tw) // 2
    y = (360 + th) // 2
    cv2.putText(img, text, (x, y), font, scale, (140, 140, 170), thickness, cv2.LINE_AA)

    # Sub-text
    sub = "Place a valid .mp4 file in project root or use webcam (source=0)"
    (sw, sh), _ = cv2.getTextSize(sub, font, 0.35, 1)
    cv2.putText(img, sub, ((640 - sw) // 2, y + 30), font, 0.35, (80, 80, 100), 1, cv2.LINE_AA)

    _, jpeg = cv2.imencode(".jpg", img)
    return jpeg.tobytes()


# Pre-generate placeholder
_PLACEHOLDER_JPEG = _make_placeholder_jpeg()


def _is_valid_video(path: str) -> bool:
    """Quick check: file exists, has reasonable size, and OpenCV can open it."""
    if not os.path.isfile(path):
        return False
    if os.path.getsize(path) < _MIN_VIDEO_SIZE:
        return False
    cap = cv2.VideoCapture(path)
    ok = cap.isOpened()
    if ok:
        ret, frame = cap.read()
        ok = ret and frame is not None
    cap.release()
    return ok


def _get_camera(model: str, source: str):
    """Instantiate the correct VideoCamera for the chosen model."""
    if model == "yolo":
        from camera_yolo import VideoCamera
    elif model == "csrnet":
        from camera_csrnet import VideoCamera
    else:
        raise ValueError(f"Unknown model: {model}. Use 'yolo' or 'csrnet'.")
    return VideoCamera(source)


async def _mjpeg_generator(camera, request: Request):
    """Yield MJPEG frames from a VideoCamera instance."""
    try:
        while True:
            if await request.is_disconnected():
                logger.info("Client disconnected from stream")
                break
                
            try:
                # Offload blocking synchronous get_frame call to thread pool
                frame = await asyncio.to_thread(camera.get_frame)
            except (AttributeError, TypeError, Exception) as e:
                # camera_csrnet.py / camera_yolo.py crash with AttributeError
                # when video source can't provide a frame (frame is None -> frame.shape)
                logger.warning(f"get_frame() error (stream ended): {e}")
                break
            if frame is None:
                break
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n"
            )
    finally:
        try:
            camera.release()
        except Exception:
            pass


def _placeholder_generator() -> Generator[bytes, None, None]:
    """Yield a single placeholder frame (no model loading required)."""
    yield (
        b"--frame\r\n"
        b"Content-Type: image/jpeg\r\n\r\n" + _PLACEHOLDER_JPEG + b"\r\n\r\n"
    )


@router.get("/stream/{model}")
async def stream_video(
    model: str,
    request: Request,
    source: str = Query("./demo.avi", description="Video file path or '0' for webcam"),
):
    """
    MJPEG streaming endpoint.

    - model: 'yolo' or 'csrnet'
    - source: path to video file or '0' for webcam
    """
    if model not in ("yolo", "csrnet"):
        raise HTTPException(status_code=400, detail="model must be 'yolo' or 'csrnet'")

    is_network_url = source.startswith(("http://", "https://", "rtsp://"))

    # Resolve relative paths against project root
    if source != "0" and not is_network_url and not os.path.isabs(source):
        source = os.path.join(PROJECT_ROOT, source)

    # For non-webcam, non-network sources, validate the video BEFORE loading the ML model
    if source != "0" and not is_network_url and not _is_valid_video(source):
        logger.warning(
            f"Video source invalid or too small: {source} "
            f"({os.path.getsize(source) if os.path.isfile(source) else 'missing'} bytes). "
            f"Serving placeholder frame."
        )
        return StreamingResponse(
            _placeholder_generator(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    try:
        camera = _get_camera(model, source)
    except Exception as e:
        logger.error(f"Failed to create camera: {e}")
        raise HTTPException(status_code=500, detail=f"Camera init failed: {e}")

    return StreamingResponse(
        _mjpeg_generator(camera, request),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
