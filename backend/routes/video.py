"""
Smart Fence - Live Video Streaming API
Provides low-latency MJPEG video streaming for the frontend dashboard
with live bounding boxes, track IDs, zone polygons, and risk annotations.
"""

import time
import logging
import cv2
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger("SmartFence.Video")

router = APIRouter(prefix="/api/video", tags=["Video Stream"])

# Global pipeline reference set by backend/main.py
active_pipeline = None


def set_pipeline(pipeline):
    global active_pipeline
    active_pipeline = pipeline


def generate_mjpeg_stream():
    """Yields multipart JPEG frames for browser <img> rendering."""
    global active_pipeline
    while True:
        if active_pipeline is not None:
            try:
                frame, _ = active_pipeline.process_frame()
                ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ret:
                    time.sleep(0.03)
                    continue

                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            except Exception as e:
                logger.error(f"Error in video streaming loop: {e}")
                time.sleep(0.1)
        else:
            time.sleep(0.1)


@router.get("/feed")
def get_video_feed():
    """MJPEG Live Video Stream with Real-Time AI Overlays."""
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/snapshot")
def get_snapshot():
    """Returns a single JPEG still frame snapshot."""
    global active_pipeline
    if active_pipeline:
        frame, _ = active_pipeline.process_frame()
        ret, buffer = cv2.imencode(".jpg", frame)
        if ret:
            return Response(content=buffer.tobytes(), media_type="image/jpeg")
    return Response(status_code=503, content="Pipeline not initialized")
