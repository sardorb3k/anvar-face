from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict
import time

from app.services.rtsp_service import get_rtsp_service
from app.services.face_service import get_face_service
from app.services.vector_service import get_vector_service
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.student import Student
from app.models.attendance import Attendance
from sqlalchemy import select, and_
from datetime import date

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections
active_connections: List[WebSocket] = []


class ConnectionManager:
    """Manages WebSocket connections with multi-face recognition support."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.rtsp_service = get_rtsp_service()
        self.face_service = get_face_service()
        self.vector_service = get_vector_service()
        self.recognition_task: asyncio.Task = None

        # Cooldown tracking: {student_id: last_recognition_timestamp}
        self.cooldown_tracker: Dict[int, float] = {}

        # Frame skip counter
        self.frame_counter: int = 0

        # Last recognition time for interval control
        self.last_recognition_time: float = 0
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_frame_mjpeg(self, websocket: WebSocket, frame: np.ndarray):
        """Send frame as MJPEG to WebSocket."""
        try:
            # Encode frame as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
            ret, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            if ret:
                # Send as binary
                await websocket.send_bytes(buffer.tobytes())
        except Exception as e:
            logger.error(f"Error sending frame: {e}")
            self.disconnect(websocket)
    
    def _is_in_cooldown(self, student_id: int) -> bool:
        """Check if student is in cooldown period."""
        if student_id not in self.cooldown_tracker:
            return False

        last_time = self.cooldown_tracker[student_id]
        elapsed = time.time() - last_time

        return elapsed < settings.COOLDOWN_SECONDS

    def _update_cooldown(self, student_id: int):
        """Update cooldown tracker for student."""
        self.cooldown_tracker[student_id] = time.time()

    def _cleanup_cooldown(self):
        """Remove expired cooldown entries to prevent memory leak."""
        current_time = time.time()
        expired = [
            sid for sid, last_time in self.cooldown_tracker.items()
            if current_time - last_time > settings.COOLDOWN_SECONDS * 2
        ]
        for sid in expired:
            del self.cooldown_tracker[sid]

    async def process_frame_recognition(self, frame: np.ndarray, timestamp: datetime):
        """Process frame for MULTI-FACE recognition and send results (Production optimized)."""
        try:
            # Extract ALL face embeddings from frame
            face_results = self.face_service.extract_all_embeddings(frame)

            if not face_results:
                # No faces detected
                await self.broadcast({
                    "type": "recognition",
                    "status": "no_face",
                    "faces_count": 0,
                    "timestamp": timestamp.isoformat()
                })
                return

            # Process each detected face
            recognized_students = []
            unknown_faces = []

            async with AsyncSessionLocal() as db:
                for embedding, face_info in face_results:
                    # Search in FAISS
                    match = self.vector_service.search_with_threshold(embedding)

                    if match is None:
                        # Unknown face
                        unknown_faces.append({
                            "bbox": face_info['bbox'],
                            "status": "unknown"
                        })
                        continue

                    student_db_id, confidence = match

                    # Check cooldown - skip if recently recognized
                    if self._is_in_cooldown(student_db_id):
                        continue

                    # Get student info
                    result = await db.execute(
                        select(Student).where(Student.id == student_db_id)
                    )
                    student = result.scalar_one_or_none()

                    if not student:
                        continue

                    # Check if already attended today
                    today = date.today()
                    result = await db.execute(
                        select(Attendance).where(
                            and_(
                                Attendance.student_id == student.id,
                                Attendance.attendance_date == today
                            )
                        )
                    )
                    existing_attendance = result.scalar_one_or_none()

                    student_data = {
                        "id": student.id,
                        "student_id": student.student_id,
                        "first_name": student.first_name,
                        "last_name": student.last_name,
                        "group_name": student.group_name,
                        "confidence": confidence,
                        "bbox": face_info['bbox']
                    }

                    if existing_attendance:
                        # Already attended today
                        student_data["status"] = "already_attended"
                        student_data["check_in_time"] = existing_attendance.check_in_time.isoformat()
                    else:
                        # Create new attendance record
                        now = datetime.now()
                        attendance = Attendance(
                            student_id=student.id,
                            attendance_date=today,
                            check_in_time=now.time(),
                            confidence_score=confidence,
                            snapshot_path=None
                        )

                        db.add(attendance)
                        await db.commit()
                        await db.refresh(attendance)

                        student_data["status"] = "success"
                        student_data["check_in_time"] = attendance.check_in_time.isoformat()
                        student_data["attendance_id"] = attendance.id

                        logger.info(f"Davomat olindi: {student.first_name} {student.last_name} ({student.student_id})")

                    # Update cooldown
                    self._update_cooldown(student_db_id)
                    recognized_students.append(student_data)

            # Cleanup old cooldown entries periodically
            if len(self.cooldown_tracker) > 100:
                self._cleanup_cooldown()

            # Broadcast results
            await self.broadcast({
                "type": "recognition",
                "status": "processed",
                "faces_count": len(face_results),
                "recognized": recognized_students,
                "unknown_count": len(unknown_faces),
                "timestamp": timestamp.isoformat()
            })

        except Exception as e:
            logger.error(f"Error in multi-face recognition: {e}")
            await self.broadcast({
                "type": "recognition",
                "status": "error",
                "message": str(e),
                "timestamp": timestamp.isoformat()
            })
    
    def _should_process_recognition(self) -> bool:
        """Check if enough time has passed for next recognition cycle."""
        current_time = time.time() * 1000  # Convert to milliseconds
        elapsed = current_time - self.last_recognition_time

        if elapsed >= settings.RECOGNITION_INTERVAL_MS:
            self.last_recognition_time = current_time
            return True
        return False

    async def start_streaming(self):
        """Start streaming frames and recognition (Production optimized)."""
        if self.recognition_task and not self.recognition_task.done():
            logger.warning("Recognition task already running")
            return

        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        def frame_callback(frame: np.ndarray, timestamp: datetime):
            """Callback for each frame from RTSP stream (with frame skip)."""
            try:
                # Increment frame counter
                self.frame_counter += 1

                # Always send frames to clients for smooth video
                asyncio.run_coroutine_threadsafe(self._send_frame_to_all(frame), loop)

                # Frame skip: only process every N-th frame
                if self.frame_counter % settings.FRAME_SKIP != 0:
                    return

                # Time-based throttling: check recognition interval
                if not self._should_process_recognition():
                    return

                # Process recognition on this frame
                asyncio.run_coroutine_threadsafe(
                    self.process_frame_recognition(frame, timestamp),
                    loop
                )

            except Exception as e:
                logger.error(f"Error in frame callback: {e}")

        # Start RTSP streaming with callback
        self.rtsp_service.start_streaming(frame_callback)

        logger.info(f"Streaming started (frame_skip={settings.FRAME_SKIP}, interval={settings.RECOGNITION_INTERVAL_MS}ms)")
    
    async def _send_frame_to_all(self, frame: np.ndarray):
        """Send frame to all connected WebSocket clients."""
        try:
            # Encode frame as JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
            ret, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            if ret:
                frame_bytes = buffer.tobytes()
                # Send to all connections
                disconnected = []
                for connection in self.active_connections:
                    try:
                        await connection.send_bytes(frame_bytes)
                    except Exception as e:
                        logger.error(f"Error sending frame: {e}")
                        disconnected.append(connection)
                
                # Remove disconnected
                for conn in disconnected:
                    self.disconnect(conn)
        except Exception as e:
            logger.error(f"Error encoding/sending frame: {e}")
    
    def stop_streaming(self):
        """Stop streaming."""
        self.rtsp_service.stop_streaming()
        logger.info("Streaming stopped")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/rtsp/stream")
async def websocket_rtsp_stream(websocket: WebSocket):
    """
    WebSocket endpoint for RTSP stream.
    Sends MJPEG frames and recognition results.
    """
    await manager.connect(websocket)
    
    try:
        # Send initial status
        status = manager.rtsp_service.get_status()
        await manager.send_personal_message({
            "type": "status",
            "connected": status["connected"],
            "running": status["running"],
            "fps": status["fps"]
        }, websocket)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/rtsp/results")
async def websocket_rtsp_results(websocket: WebSocket):
    """
    WebSocket endpoint for recognition results only.
    Lightweight connection for results without video stream.
    """
    await manager.connect(websocket)
    
    try:
        while True:
            try:
                # Just keep connection alive
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)

