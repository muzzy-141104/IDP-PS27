#!/usr/bin/env python3
"""
Raspberry Pi MJPEG Streamer

This script captures frames from a webcam and streams them over HTTP.
It is designed to be lightweight so the Raspberry Pi does not overheat or lag.

Prerequisites:
    pip install flask opencv-python

Usage:
    python3 rpi_streamer.py --port 5000 --resolution 640x480 --fps 15
"""

import cv2
import argparse
import time
from flask import Flask, Response

app = Flask(__name__)

# Global variables for the camera settings
CAMERA_SOURCE = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 640
TARGET_FPS = 15

def enhance_contrast(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return enhanced

def get_frames():
    """Generator function that continuously reads frames from the camera."""
    camera = cv2.VideoCapture(CAMERA_SOURCE)
    
    # Try to set camera resolution and FPS
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, TARGET_FPS)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    print(f"Camera opened successfully. Resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}")

    # Calculate target frame delay
    frame_delay = 1.0 / TARGET_FPS

    while True:
        start_time = time.time()
        success, frame = camera.read()
        
        if not success:
            print("Warning: Failed to read frame from camera. Retrying...")
            time.sleep(0.5)
            continue
            
        # Resize according to YOLO input
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Contrast enhancement
        enhanced = enhance_contrast(frame)
            
        # Encode the frame in JPEG format
        # Lower quality (e.g., 70) reduces bandwidth and latency
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        ret, buffer = cv2.imencode('.jpg', enhanced, encode_param)
        
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        # Yield the output frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        # Control the FPS
        elapsed = time.time() - start_time
        if elapsed < frame_delay:
            time.sleep(frame_delay - elapsed)

@app.route('/video_feed')
def video_feed():
    """HTTP endpoint returning the MJPEG stream."""
    return Response(get_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Crowd Management</title>
        </head>
        <body>
            <h1>Crowd Management</h1>
            <img src="/video_feed" width="700">
        </body>
    </html>
    '''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Raspberry Pi MJPEG Streamer")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the stream on")
    parser.add_argument("--resolution", type=str, default="640x640", help="Camera resolution (WxH)")
    parser.add_argument("--fps", type=int, default=15, help="Target frames per second")
    parser.add_argument("--source", type=int, default=0, help="Webcam device ID (default: 0)")
    args = parser.parse_args()

    # Parse resolution
    try:
        w, h = map(int, args.resolution.lower().split('x'))
        FRAME_WIDTH = w
        FRAME_HEIGHT = h
    except ValueError:
        print("Invalid resolution format. Using default 640x640.")

    TARGET_FPS = args.fps
    CAMERA_SOURCE = args.source

    print(f"Starting stream on 0.0.0.0:{args.port}/video_feed")
    print("Press Ctrl+C to stop.")
    
    # Run the Flask app on all network interfaces
    app.run(host='0.0.0.0', port=args.port, threaded=True)
