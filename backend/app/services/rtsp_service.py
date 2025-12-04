import cv2
import numpy as np
import asyncio
import logging
from typing import Optional, Callable, Tuple
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)


class RTSPStreamService:
    """RTSP stream service for reading and processing video frames."""
    
    def __init__(self):
        self.capture: Optional[cv2.VideoCapture] = None
        self.rtsp_url: Optional[str] = None
        self.is_connected: bool = False
        self.is_running: bool = False
        self.frame_callback: Optional[Callable] = None
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.last_frame: Optional[np.ndarray] = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
    
    def connect(self, rtsp_url: str, timeout: int = 30) -> bool:
        """
        Connect to RTSP stream.
        
        Args:
            rtsp_url: RTSP stream URL (e.g., rtsp://user:pass@ip:port/stream)
            timeout: Connection timeout in seconds
            
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            logger.info(f"Connecting to RTSP stream: {rtsp_url}")
            
            # Create VideoCapture with RTSP URL
            self.capture = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            # Set buffer size to reduce latency
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Set timeout
            start_time = time.time()
            while not self.capture.isOpened():
                if time.time() - start_time > timeout:
                    logger.error(f"RTSP connection timeout after {timeout} seconds")
                    self.disconnect()
                    return False
                time.sleep(0.1)
            
            # Test read
            ret, frame = self.capture.read()
            if not ret or frame is None:
                logger.error("Failed to read first frame from RTSP stream")
                self.disconnect()
                return False
            
            self.rtsp_url = rtsp_url
            self.is_connected = True
            self.last_frame = frame
            
            logger.info("RTSP stream connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to RTSP stream: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from RTSP stream."""
        self.is_running = False
        self.is_connected = False
        
        if self.thread and self.thread.is_alive():
            # Wait for thread to finish
            self.thread.join(timeout=2)
        
        if self.capture:
            try:
                self.capture.release()
            except Exception as e:
                logger.error(f"Error releasing capture: {e}")
            self.capture = None
        
        self.rtsp_url = None
        self.last_frame = None
        self.frame_count = 0
        logger.info("RTSP stream disconnected")
    
    def start_streaming(self, frame_callback: Optional[Callable] = None):
        """
        Start streaming frames in background thread.
        
        Args:
            frame_callback: Callback function(frame, timestamp) called for each frame
        """
        if not self.is_connected:
            logger.error("Cannot start streaming: not connected")
            return
        
        if self.is_running:
            logger.warning("Streaming already running")
            return
        
        self.frame_callback = frame_callback
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()
        logger.info("RTSP streaming started")
    
    def stop_streaming(self):
        """Stop streaming frames."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        logger.info("RTSP streaming stopped")
    
    def _stream_loop(self):
        """Background thread loop for reading frames."""
        while self.is_running and self.is_connected:
            try:
                if not self.capture or not self.capture.isOpened():
                    logger.error("Capture not available")
                    break
                
                ret, frame = self.capture.read()
                
                if not ret or frame is None:
                    logger.warning("Failed to read frame, attempting reconnection...")
                    # Try to reconnect
                    if self.rtsp_url:
                        self.capture.release()
                        time.sleep(1)
                        self.capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    continue
                
                # Update frame
                with self.lock:
                    self.last_frame = frame.copy()
                    self.frame_count += 1
                
                # Calculate FPS
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_time = current_time
                
                # Call callback if provided
                if self.frame_callback:
                    try:
                        self.frame_callback(frame, datetime.now())
                    except Exception as e:
                        logger.error(f"Error in frame callback: {e}")
                
                # Small delay to prevent CPU overload
                time.sleep(0.01)  # ~100 FPS max
                
            except Exception as e:
                logger.error(f"Error in stream loop: {e}")
                time.sleep(0.1)
        
        logger.info("Stream loop ended")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get latest frame from stream.
        
        Returns:
            Latest frame as numpy array or None
        """
        with self.lock:
            if self.last_frame is not None:
                return self.last_frame.copy()
            return None
    
    def get_status(self) -> dict:
        """
        Get stream status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "connected": self.is_connected,
            "running": self.is_running,
            "rtsp_url": self.rtsp_url,
            "fps": self.fps,
            "frame_count": self.frame_count
        }
    
    def encode_frame_jpeg(self, frame: np.ndarray, quality: int = 85) -> bytes:
        """
        Encode frame as JPEG for MJPEG streaming.
        
        Args:
            frame: Frame as numpy array
            quality: JPEG quality (0-100)
            
        Returns:
            JPEG encoded frame as bytes
        """
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        ret, buffer = cv2.imencode('.jpg', frame, encode_params)
        if ret:
            return buffer.tobytes()
        return b''


# Global RTSP service instance
_rtsp_service: Optional[RTSPStreamService] = None


def get_rtsp_service() -> RTSPStreamService:
    """Get or create global RTSP service instance."""
    global _rtsp_service
    if _rtsp_service is None:
        _rtsp_service = RTSPStreamService()
    return _rtsp_service

