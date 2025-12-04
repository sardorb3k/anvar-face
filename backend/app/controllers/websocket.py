from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict

from app.services.rtsp_service import get_rtsp_service
from app.services.face_service import get_face_service
from app.services.vector_service import get_vector_service
from app.core.database import AsyncSessionLocal
from app.models.student import Student
from app.models.attendance import Attendance
from sqlalchemy import select, and_
from datetime import date

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections
active_connections: List[WebSocket] = []


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.rtsp_service = get_rtsp_service()
        self.face_service = get_face_service()
        self.vector_service = get_vector_service()
        self.recognition_task: asyncio.Task = None
        self.last_recognition_time = {}
    
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
    
    async def process_frame_recognition(self, frame: np.ndarray, timestamp: datetime):
        """Process frame for face recognition and send results."""
        try:
            # Extract embedding
            embedding = self.face_service.extract_embedding(frame)
            
            if embedding is None:
                # No face detected
                await self.broadcast({
                    "type": "recognition",
                    "status": "no_face",
                    "timestamp": timestamp.isoformat()
                })
                return
            
            # Search in FAISS
            match = self.vector_service.search_with_threshold(embedding)
            
            if match is None:
                # No match found
                await self.broadcast({
                    "type": "recognition",
                    "status": "not_found",
                    "confidence": 0,
                    "timestamp": timestamp.isoformat()
                })
                return
            
            student_db_id, confidence = match
            
            # Get student info from database
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Student).where(Student.id == student_db_id)
                )
                student = result.scalar_one_or_none()
                
                if not student:
                    await self.broadcast({
                        "type": "recognition",
                        "status": "error",
                        "message": "Student not found in database",
                        "timestamp": timestamp.isoformat()
                    })
                    return
                
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
                
                if existing_attendance:
                    # Already attended
                    await self.broadcast({
                        "type": "recognition",
                        "status": "already_attended",
                        "student": {
                            "id": student.id,
                            "student_id": student.student_id,
                            "first_name": student.first_name,
                            "last_name": student.last_name,
                            "group_name": student.group_name
                        },
                        "confidence": confidence,
                        "check_in_time": existing_attendance.check_in_time.isoformat(),
                        "timestamp": timestamp.isoformat()
                    })
                else:
                    # Create attendance record
                    now = datetime.now()
                    attendance = Attendance(
                        student_id=student.id,
                        attendance_date=today,
                        check_in_time=now.time(),
                        confidence_score=confidence,
                        snapshot_path=None  # Can save snapshot if needed
                    )
                    
                    db.add(attendance)
                    await db.commit()
                    
                    # Broadcast success
                    await self.broadcast({
                        "type": "recognition",
                        "status": "success",
                        "student": {
                            "id": student.id,
                            "student_id": student.student_id,
                            "first_name": student.first_name,
                            "last_name": student.last_name,
                            "group_name": student.group_name
                        },
                        "confidence": confidence,
                        "check_in_time": attendance.check_in_time.isoformat(),
                        "attendance_id": attendance.id,
                        "timestamp": timestamp.isoformat()
                    })
        
        except Exception as e:
            logger.error(f"Error in recognition processing: {e}")
            await self.broadcast({
                "type": "recognition",
                "status": "error",
                "message": str(e),
                "timestamp": timestamp.isoformat()
            })
    
    async def start_streaming(self):
        """Start streaming frames and recognition."""
        if self.recognition_task and not self.recognition_task.done():
            logger.warning("Recognition task already running")
            return
        
        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        
        def frame_callback(frame: np.ndarray, timestamp: datetime):
            """Callback for each frame from RTSP stream."""
            # Use asyncio.run_coroutine_threadsafe for thread-safe async calls
            try:
                # Send frame to all connected clients
                asyncio.run_coroutine_threadsafe(self._send_frame_to_all(frame), loop)
                
                # Process recognition (continuous - every frame)
                asyncio.run_coroutine_threadsafe(self.process_frame_recognition(frame, timestamp), loop)
            except Exception as e:
                logger.error(f"Error in frame callback: {e}")
        
        # Start RTSP streaming with callback
        self.rtsp_service.start_streaming(frame_callback)
        
        logger.info("Streaming and recognition started")
    
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

