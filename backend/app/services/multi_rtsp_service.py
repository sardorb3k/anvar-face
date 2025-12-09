import cv2
import numpy as np
import logging
from typing import Optional, Callable, Dict
from datetime import datetime
import threading
import time

from app.core.config import settings

logger = logging.getLogger(__name__)


class RTSPStreamInstance:
    """Individual RTSP stream instance for a single camera."""

    def __init__(self, camera_id: int, rtsp_url: str, room_id: int):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.room_id = room_id
        self.capture: Optional[cv2.VideoCapture] = None
        self.is_connected: bool = False
        self.is_running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.last_frame: Optional[np.ndarray] = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_callback: Optional[Callable] = None

    def connect(self, timeout: int = 30) -> bool:
        """Connect to RTSP stream."""
        try:
            logger.info(f"Camera {self.camera_id}: Connecting to {self.rtsp_url}")

            # RTSP stream uchun optimallashtirilgan sozlamalar
            self.capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)

            # Buffer hajmini minimal qilish - lag ni kamaytiradi
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # RTSP transport protokoli - TCP ishonchliroq
            self.capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
            self.capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)

            # Frame size optimization
            # self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            # self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            start_time = time.time()
            while not self.capture.isOpened():
                if time.time() - start_time > timeout:
                    logger.error(f"Camera {self.camera_id}: Connection timeout")
                    self.disconnect()
                    return False
                time.sleep(0.1)

            ret, frame = self.capture.read()
            if not ret or frame is None:
                logger.error(f"Camera {self.camera_id}: Failed to read first frame")
                self.disconnect()
                return False

            self.is_connected = True
            self.last_frame = frame
            logger.info(f"Camera {self.camera_id}: Connected successfully")
            return True

        except Exception as e:
            logger.error(f"Camera {self.camera_id}: Connection error - {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """Disconnect from RTSP stream."""
        self.is_running = False
        self.is_connected = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)

        if self.capture:
            try:
                self.capture.release()
            except Exception as e:
                logger.error(f"Camera {self.camera_id}: Release error - {e}")
            self.capture = None

        self.last_frame = None
        self.frame_count = 0
        logger.info(f"Camera {self.camera_id}: Disconnected")

    def start_streaming(self, frame_callback: Optional[Callable] = None):
        """Start streaming in background thread."""
        if not self.is_connected:
            logger.error(f"Camera {self.camera_id}: Cannot start - not connected")
            return

        if self.is_running:
            logger.warning(f"Camera {self.camera_id}: Already streaming")
            return

        self.frame_callback = frame_callback
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        logger.info(f"Camera {self.camera_id}: Streaming started")

    def stop_streaming(self):
        """Stop streaming."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        logger.info(f"Camera {self.camera_id}: Streaming stopped")

    def _stream_loop(self):
        """Background thread loop for reading frames."""
        reconnect_attempts = 0
        max_reconnect_attempts = 10  # Ko'proq urinishlar
        consecutive_fails = 0
        max_consecutive_fails = 3  # 3 ta ketma-ket xatolikdan keyin reconnect

        try:
            while self.is_running and self.is_connected:
                try:
                    if not self.capture or not self.capture.isOpened():
                        logger.error(f"Camera {self.camera_id}: Capture not available")
                        break

                    # Grab va retrieve alohida - buffer tozalash uchun
                    ret = self.capture.grab()

                    if not ret:
                        consecutive_fails += 1
                        if consecutive_fails >= max_consecutive_fails:
                            reconnect_attempts += 1
                            logger.warning(
                                f"Camera {self.camera_id}: Frame read failed, "
                                f"reconnect attempt {reconnect_attempts}/{max_reconnect_attempts}"
                            )

                            if reconnect_attempts >= max_reconnect_attempts:
                                logger.error(f"Camera {self.camera_id}: Max reconnect attempts reached")
                                break

                            # Try to reconnect
                            if self.capture:
                                try:
                                    self.capture.release()
                                except:
                                    pass
                            time.sleep(0.5)  # Qisqaroq kutish
                            self.capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                            self.capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
                            self.capture.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
                            consecutive_fails = 0
                        continue

                    # Retrieve frame
                    ret, frame = self.capture.retrieve()
                    if not ret or frame is None:
                        consecutive_fails += 1
                        continue

                    # Success - reset counters
                    consecutive_fails = 0
                    reconnect_attempts = 0

                    # Don't copy frame unless needed - just reference
                    with self.lock:
                        self.last_frame = frame  # No copy for internal storage
                        self.frame_count += 1

                    # Calculate FPS
                    current_time = time.time()
                    if current_time - self.last_fps_time >= 1.0:
                        self.fps = self.frame_count
                        self.frame_count = 0
                        self.last_fps_time = current_time

                    # Call callback with room_id and camera_id
                    if self.frame_callback:
                        try:
                            self.frame_callback(
                                frame,
                                datetime.now(),
                                self.room_id,
                                self.camera_id
                            )
                        except Exception as e:
                            logger.error(f"Camera {self.camera_id}: Callback error - {e}")

                    time.sleep(0.033)  # ~30 FPS max - barqaror stream uchun

                except Exception as e:
                    logger.error(f"Camera {self.camera_id}: Stream loop error - {e}")
                    time.sleep(0.1)

        finally:
            # CRITICAL: Always release capture when loop ends
            if self.capture:
                try:
                    self.capture.release()
                    logger.info(f"Camera {self.camera_id}: Capture released in finally block")
                except Exception as e:
                    logger.error(f"Camera {self.camera_id}: Error releasing capture - {e}")
                self.capture = None

            self.is_connected = False
            self.last_frame = None  # Free memory
            logger.info(f"Camera {self.camera_id}: Stream loop ended")

    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame."""
        with self.lock:
            if self.last_frame is not None:
                return self.last_frame.copy()
            return None

    def get_status(self) -> dict:
        """Get stream status."""
        return {
            "camera_id": self.camera_id,
            "room_id": self.room_id,
            "connected": self.is_connected,
            "running": self.is_running,
            "rtsp_url": self.rtsp_url,
            "fps": self.fps
        }


class MultiRTSPStreamManager:
    """Manages multiple RTSP streams for room monitoring."""

    def __init__(self):
        self.streams: Dict[int, RTSPStreamInstance] = {}  # camera_id -> stream instance
        self.lock = threading.Lock()
        logger.info("MultiRTSPStreamManager initialized")

    def start_camera(
        self,
        camera_id: int,
        rtsp_url: str,
        room_id: int,
        frame_callback: Optional[Callable] = None,
        timeout: int = 30
    ) -> bool:
        """
        Start streaming from a camera.

        Args:
            camera_id: Camera ID from database
            rtsp_url: RTSP stream URL
            room_id: Room ID this camera belongs to
            frame_callback: Callback function(frame, timestamp, room_id, camera_id)
            timeout: Connection timeout in seconds

        Returns:
            True if started successfully
        """
        with self.lock:
            if len(self.streams) >= settings.MAX_SIMULTANEOUS_STREAMS:
                logger.error(f"Max simultaneous streams ({settings.MAX_SIMULTANEOUS_STREAMS}) reached")
                return False

            if camera_id in self.streams:
                logger.warning(f"Camera {camera_id} already streaming")
                return True

            stream = RTSPStreamInstance(camera_id, rtsp_url, room_id)

            if not stream.connect(timeout):
                return False

            stream.start_streaming(frame_callback)
            self.streams[camera_id] = stream

            logger.info(f"Camera {camera_id} started. Total active streams: {len(self.streams)}")
            return True

    def stop_camera(self, camera_id: int) -> bool:
        """Stop streaming from a camera."""
        with self.lock:
            if camera_id not in self.streams:
                logger.warning(f"Camera {camera_id} not found in active streams")
                return False

            stream = self.streams[camera_id]
            stream.stop_streaming()
            stream.disconnect()
            del self.streams[camera_id]

            logger.info(f"Camera {camera_id} stopped. Total active streams: {len(self.streams)}")
            return True

    def stop_room_cameras(self, room_id: int) -> int:
        """Stop all cameras in a room. Returns count of stopped cameras."""
        stopped = 0
        with self.lock:
            cameras_to_stop = [
                cam_id for cam_id, stream in self.streams.items()
                if stream.room_id == room_id
            ]

        for cam_id in cameras_to_stop:
            if self.stop_camera(cam_id):
                stopped += 1

        return stopped

    def stop_all(self):
        """Stop all streams."""
        with self.lock:
            camera_ids = list(self.streams.keys())

        for camera_id in camera_ids:
            self.stop_camera(camera_id)

        logger.info("All streams stopped")

    def get_camera_status(self, camera_id: int) -> Optional[dict]:
        """Get status of a specific camera."""
        with self.lock:
            if camera_id in self.streams:
                return self.streams[camera_id].get_status()
            return None

    def get_camera_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """Get latest frame from a camera."""
        with self.lock:
            if camera_id in self.streams:
                return self.streams[camera_id].get_frame()
            return None

    def get_all_statuses(self) -> Dict[int, dict]:
        """Get status of all cameras."""
        with self.lock:
            return {
                cam_id: stream.get_status()
                for cam_id, stream in self.streams.items()
            }

    def get_room_cameras(self, room_id: int) -> Dict[int, dict]:
        """Get status of all cameras in a room."""
        with self.lock:
            return {
                cam_id: stream.get_status()
                for cam_id, stream in self.streams.items()
                if stream.room_id == room_id
            }

    def is_camera_active(self, camera_id: int) -> bool:
        """Check if a camera is active."""
        with self.lock:
            return camera_id in self.streams and self.streams[camera_id].is_running

    def get_active_count(self) -> int:
        """Get count of active streams."""
        with self.lock:
            return len(self.streams)

    @staticmethod
    def encode_frame_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
        """Encode frame as JPEG."""
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        ret, buffer = cv2.imencode('.jpg', frame, encode_params)
        if ret:
            return buffer.tobytes()
        return b''


# Global instance
_multi_rtsp_manager: Optional[MultiRTSPStreamManager] = None


def get_multi_rtsp_manager() -> MultiRTSPStreamManager:
    """Get or create global MultiRTSPStreamManager instance."""
    global _multi_rtsp_manager
    if _multi_rtsp_manager is None:
        _multi_rtsp_manager = MultiRTSPStreamManager()
    return _multi_rtsp_manager
