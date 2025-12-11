from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio
import json
import logging
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Set, Optional
from collections import defaultdict
import time

from app.services.multi_rtsp_service import get_multi_rtsp_manager
from app.services.face_service import get_face_service
from app.services.vector_service import get_vector_service
from app.services.presence_service import get_presence_service
from app.services.room_service import get_room_service
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.student import Student

logger = logging.getLogger(__name__)

router = APIRouter()


class RoomConnectionManager:
    """Manages WebSocket connections for room monitoring with multi-face recognition."""

    def __init__(self):
        # room_id -> set of WebSocket connections (for presence updates)
        self.room_subscriptions: Dict[int, Set[WebSocket]] = defaultdict(set)

        # camera_id -> set of WebSocket connections (for video streams)
        self.camera_subscriptions: Dict[int, Set[WebSocket]] = defaultdict(set)

        # All presence subscribers (for dashboard)
        self.all_presence_subscribers: Set[WebSocket] = set()

        # Services
        self.rtsp_manager = get_multi_rtsp_manager()
        self.face_service = get_face_service()
        self.vector_service = get_vector_service()
        self.presence_service = get_presence_service()
        self.room_service = get_room_service()

        # Cooldown tracking per room: {room_id: {student_id: timestamp}}
        self.room_cooldowns: Dict[int, Dict[int, float]] = defaultdict(dict)

        # Guest tracking per room: {room_id: {guest_hash: timestamp}}
        # Guest hash dan bbox koordinatalari asosida yaratiladi
        self.guest_tracking: Dict[int, Dict[str, float]] = defaultdict(dict)

        # Frame counters per camera
        self.frame_counters: Dict[int, int] = defaultdict(int)

        # Last recognition time per camera
        self.last_recognition_time: Dict[int, float] = defaultdict(float)

        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

        # PERFORMANCE FIX: Periodic cleanup tracking
        self._last_dict_cleanup = time.time()
        self._dict_cleanup_interval = 60  # Cleanup every 60 seconds

        # PERFORMANCE FIX: Max pending tasks limit
        self._max_pending_tasks = 50

        logger.info("RoomConnectionManager initialized")

    # ==================== Connection Management ====================

    async def subscribe_room_presence(self, websocket: WebSocket, room_id: int):
        """Subscribe to presence updates for a specific room."""
        await websocket.accept()
        self.room_subscriptions[room_id].add(websocket)
        logger.info(f"WebSocket subscribed to room {room_id} presence. "
                    f"Total subscribers: {len(self.room_subscriptions[room_id])}")

    async def subscribe_camera_stream(self, websocket: WebSocket, camera_id: int):
        """Subscribe to video stream from a specific camera."""
        await websocket.accept()
        self.camera_subscriptions[camera_id].add(websocket)
        logger.info(f"WebSocket subscribed to camera {camera_id} stream. "
                    f"Total subscribers: {len(self.camera_subscriptions[camera_id])}")

    async def subscribe_all_presence(self, websocket: WebSocket):
        """Subscribe to presence updates for all rooms (dashboard)."""
        await websocket.accept()
        self.all_presence_subscribers.add(websocket)
        logger.info(f"WebSocket subscribed to all presence. "
                    f"Total subscribers: {len(self.all_presence_subscribers)}")

    def unsubscribe_room(self, websocket: WebSocket, room_id: int):
        """Unsubscribe from room presence."""
        self.room_subscriptions[room_id].discard(websocket)
        # PERFORMANCE FIX: Clean up empty entries
        if not self.room_subscriptions[room_id]:
            del self.room_subscriptions[room_id]
        logger.info(f"WebSocket unsubscribed from room {room_id}")

    def unsubscribe_camera(self, websocket: WebSocket, camera_id: int):
        """Unsubscribe from camera stream."""
        self.camera_subscriptions[camera_id].discard(websocket)
        # PERFORMANCE FIX: Clean up empty entries
        if not self.camera_subscriptions[camera_id]:
            del self.camera_subscriptions[camera_id]
        logger.info(f"WebSocket unsubscribed from camera {camera_id}")

    def unsubscribe_all_presence(self, websocket: WebSocket):
        """Unsubscribe from all presence updates."""
        self.all_presence_subscribers.discard(websocket)
        logger.info("WebSocket unsubscribed from all presence")

    # ==================== Broadcasting ====================

    async def broadcast_to_room(self, room_id: int, message: dict):
        """Broadcast message to all subscribers of a room."""
        disconnected = []
        for ws in self.room_subscriptions[room_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to room {room_id}: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.room_subscriptions[room_id].discard(ws)

    async def broadcast_camera_frame(self, camera_id: int, frame_bytes: bytes):
        """Broadcast frame to all subscribers of a camera."""
        disconnected = []
        for ws in self.camera_subscriptions[camera_id]:
            try:
                await ws.send_bytes(frame_bytes)
            except Exception as e:
                logger.error(f"Error broadcasting to camera {camera_id}: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.camera_subscriptions[camera_id].discard(ws)

    async def broadcast_to_camera(self, camera_id: int, message: dict):
        """Broadcast JSON message to all subscribers of a camera (e.g., face detections)."""
        if camera_id not in self.camera_subscriptions:
            return
        
        disconnected = []
        for ws in self.camera_subscriptions[camera_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting JSON to camera {camera_id}: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.camera_subscriptions[camera_id].discard(ws)

    async def broadcast_all_presence(self, message: dict):
        """Broadcast to all presence subscribers (dashboard)."""
        disconnected = []
        for ws in self.all_presence_subscribers:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting all presence: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.all_presence_subscribers.discard(ws)

    # ==================== Recognition & Presence ====================

    def _is_in_cooldown(self, room_id: int, student_id: int) -> bool:
        """Check if student is in cooldown for this room."""
        if room_id not in self.room_cooldowns:
            return False
        if student_id not in self.room_cooldowns[room_id]:
            return False

        last_time = self.room_cooldowns[room_id][student_id]
        elapsed = time.time() - last_time
        return elapsed < settings.COOLDOWN_SECONDS

    def _update_cooldown(self, room_id: int, student_id: int):
        """Update cooldown for student in room."""
        self.room_cooldowns[room_id][student_id] = time.time()

    def _cleanup_cooldowns(self):
        """Remove expired cooldown entries."""
        current_time = time.time()
        for room_id in list(self.room_cooldowns.keys()):
            expired = [
                sid for sid, last_time in self.room_cooldowns[room_id].items()
                if current_time - last_time > settings.COOLDOWN_SECONDS * 2
            ]
            for sid in expired:
                del self.room_cooldowns[room_id][sid]

            if not self.room_cooldowns[room_id]:
                del self.room_cooldowns[room_id]

    def _cleanup_guests(self):
        """Clean up old guest entries (older than timeout)."""
        cleanup_threshold = time.time() - settings.PRESENCE_TIMEOUT_SECONDS
        
        for room_id in list(self.guest_tracking.keys()):
            guests = self.guest_tracking[room_id]
            # Remove old entries
            old_keys = [k for k, v in guests.items() if v < cleanup_threshold]
            for key in old_keys:
                del guests[key]
            
            # Remove empty room entries
            if not guests:
                del self.guest_tracking[room_id]

    def _get_guest_hash(self, bbox: list) -> str:
        """Create a hash for guest tracking based on approximate bbox location."""
        # Bbox ni yaxlitlash - bir xil odamni tracking qilish uchun
        # Bbox: [x1, y1, x2, y2]
        x_center = int((bbox[0] + bbox[2]) / 2 / 50) * 50  # 50px tolerance
        y_center = int((bbox[1] + bbox[3]) / 2 / 50) * 50
        return f"{x_center}_{y_center}"

    def _update_guest_tracking(self, room_id: int, guest_hash: str):
        """Update guest last seen time."""
        self.guest_tracking[room_id][guest_hash] = time.time()

    def _get_active_guests_count(self, room_id: int) -> int:
        """Get count of active guests in room."""
        if room_id not in self.guest_tracking:
            return 0
        
        cutoff_time = time.time() - settings.PRESENCE_TIMEOUT_SECONDS
        active_guests = sum(
            1 for timestamp in self.guest_tracking[room_id].values()
            if timestamp >= cutoff_time
        )
        return active_guests

    def _cleanup_all_dicts(self):
        """PERFORMANCE FIX: Clean all tracking dictionaries periodically."""
        # Cleanup cooldowns
        self._cleanup_cooldowns()
        
        # Cleanup guests
        self._cleanup_guests()

        # Cleanup frame counters - only keep active cameras
        active_cameras = set(self.rtsp_manager.streams.keys()) if hasattr(self.rtsp_manager, 'streams') else set()

        # Remove counters for inactive cameras
        for cam_id in list(self.frame_counters.keys()):
            if cam_id not in active_cameras:
                del self.frame_counters[cam_id]

        for cam_id in list(self.last_recognition_time.keys()):
            if cam_id not in active_cameras:
                del self.last_recognition_time[cam_id]

        # Cleanup empty subscription entries
        for room_id in list(self.room_subscriptions.keys()):
            if not self.room_subscriptions[room_id]:
                del self.room_subscriptions[room_id]

        for cam_id in list(self.camera_subscriptions.keys()):
            if not self.camera_subscriptions[cam_id]:
                del self.camera_subscriptions[cam_id]

        logger.info(f"Dict cleanup done. Cooldowns: {len(self.room_cooldowns)}, "
                    f"Frame counters: {len(self.frame_counters)}, "
                    f"Subscriptions: rooms={len(self.room_subscriptions)}, cameras={len(self.camera_subscriptions)}")

    def _should_process_recognition(self, camera_id: int) -> bool:
        """Check if enough time has passed for recognition on this camera."""
        current_time = time.time() * 1000
        elapsed = current_time - self.last_recognition_time[camera_id]

        if elapsed >= settings.RECOGNITION_INTERVAL_MS:
            self.last_recognition_time[camera_id] = current_time
            return True
        return False

    async def process_frame_for_presence(
        self,
        frame: np.ndarray,
        timestamp: datetime,
        room_id: int,
        camera_id: int
    ):
        """Process frame for face recognition and update room presence."""
        try:
            # Extract all face embeddings
            face_results = self.face_service.extract_all_embeddings(frame)

            if not face_results:
                return

            recognized_students = []
            all_faces = []  # Barcha yuzlar (tanilgan va tanilmagan)

            async with AsyncSessionLocal() as db:
                for embedding, face_info in face_results:
                    # Search in FAISS
                    match = self.vector_service.search_with_threshold(embedding)

                    if match is None:
                        # Tanilmagan yuz - "Mehmon"
                        # Track guest for counting
                        guest_hash = self._get_guest_hash(face_info['bbox'])
                        self._update_guest_tracking(room_id, guest_hash)
                        
                        all_faces.append({
                            "type": "guest",
                            "label": "Mehmon",
                            "bbox": face_info['bbox'],
                            "confidence": 0.0
                        })
                        continue

                    student_db_id, confidence = match

                    # Get student info
                    result = await db.execute(
                        select(Student).where(Student.id == student_db_id)
                    )
                    student = result.scalar_one_or_none()

                    if not student:
                        all_faces.append({
                            "type": "guest",
                            "label": "Mehmon",
                            "bbox": face_info['bbox'],
                            "confidence": 0.0
                        })
                        continue

                    # Tanilgan yuz - ism-familiya bilan
                    all_faces.append({
                        "type": "student",
                        "label": f"{student.first_name} {student.last_name}",
                        "student_id": student.student_id,
                        "bbox": face_info['bbox'],
                        "confidence": confidence
                    })

                    # Check cooldown for database update
                    if self._is_in_cooldown(room_id, student_db_id):
                        continue

                    # Update presence in database
                    await self.presence_service.update_presence(
                        db, student_db_id, room_id, camera_id, confidence
                    )
                    await db.commit()

                    # Update cooldown
                    self._update_cooldown(room_id, student_db_id)

                    recognized_students.append({
                        "student_id": student.id,
                        "student_number": student.student_id,
                        "first_name": student.first_name,
                        "last_name": student.last_name,
                        "group_name": student.group_name,
                        "confidence": confidence,
                        "camera_id": camera_id
                    })

                    logger.info(
                        f"Presence updated: {student.first_name} {student.last_name} "
                        f"in Room {room_id} (Camera {camera_id})"
                    )

            # Broadcast presence update if any recognized
            if recognized_students:
                # Get room name
                async with AsyncSessionLocal() as db:
                    room = await self.room_service.get_room(db, room_id)
                    room_name = room.name if room else f"Room {room_id}"

                    # Get current room presence
                    presence_list = await self.presence_service.get_room_presence(db, room_id)

                # Get guest count
                guest_count = self._get_active_guests_count(room_id)
                total_people = len(presence_list) + guest_count

                presence_message = {
                    "type": "presence_update",
                    "room_id": room_id,
                    "room_name": room_name,
                    "new_recognitions": recognized_students,
                    "occupants": [p.to_dict() for p in presence_list],
                    "total_count": len(presence_list),
                    "guest_count": guest_count,
                    "total_people": total_people,
                    "timestamp": timestamp.isoformat()
                }

                # Broadcast to room subscribers
                await self.broadcast_to_room(room_id, presence_message)

                # Broadcast to all presence subscribers
                await self.broadcast_all_presence(presence_message)

            # Har doim yuzlarni yuborish (video stream uchun)
            if all_faces:
                face_detection_message = {
                    "type": "face_detection",
                    "camera_id": camera_id,
                    "faces": all_faces,
                    "total_faces": len(all_faces),
                    "timestamp": timestamp.isoformat()
                }
                
                # Broadcast face detections to camera subscribers
                await self.broadcast_to_camera(camera_id, face_detection_message)

            # Cleanup cooldowns periodically
            if sum(len(c) for c in self.room_cooldowns.values()) > 100:
                self._cleanup_cooldowns()

        except Exception as e:
            logger.error(f"Error in presence recognition: {e}")

    def create_frame_callback(self, loop: asyncio.AbstractEventLoop):
        """Create frame callback for RTSP streaming."""

        def frame_callback(
            frame: np.ndarray,
            timestamp: datetime,
            room_id: int,
            camera_id: int
        ):
            """Callback for each frame from camera."""
            try:
                # PERFORMANCE FIX: Backpressure - skip if too many pending tasks
                try:
                    pending_tasks = len([t for t in asyncio.all_tasks(loop) if not t.done()])
                    if pending_tasks > self._max_pending_tasks:
                        # Skip this frame entirely to reduce load
                        return
                except RuntimeError:
                    # Loop might be closed, skip
                    pass

                # PERFORMANCE FIX: Periodic dictionary cleanup
                current_time = time.time()
                if current_time - self._last_dict_cleanup > self._dict_cleanup_interval:
                    self._cleanup_all_dicts()
                    self._last_dict_cleanup = current_time

                # Increment frame counter
                self.frame_counters[camera_id] += 1

                # Only broadcast frames if there are subscribers
                if self.camera_subscriptions.get(camera_id):
                    # Encode and send frame to subscribers
                    frame_bytes = self.rtsp_manager.encode_frame_jpeg(frame)
                    if frame_bytes:
                        asyncio.run_coroutine_threadsafe(
                            self.broadcast_camera_frame(camera_id, frame_bytes),
                            loop
                        )

                # Frame skip for recognition
                if self.frame_counters[camera_id] % settings.FRAME_SKIP != 0:
                    return

                # Time-based throttling
                if not self._should_process_recognition(camera_id):
                    return

                # Process recognition
                asyncio.run_coroutine_threadsafe(
                    self.process_frame_for_presence(frame, timestamp, room_id, camera_id),
                    loop
                )

            except Exception as e:
                logger.error(f"Error in frame callback: {e}")

        return frame_callback

    # ==================== Camera Control ====================

    async def start_camera_with_callback(
        self,
        camera_id: int,
        rtsp_url: str,
        room_id: int,
        timeout: int = 30
    ) -> bool:
        """Start camera with recognition callback."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        callback = self.create_frame_callback(loop)

        success = self.rtsp_manager.start_camera(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            room_id=room_id,
            frame_callback=callback,
            timeout=timeout
        )

        if success:
            logger.info(f"Camera {camera_id} started with presence callback")

        return success

    # ==================== Background Cleanup ====================

    async def start_cleanup_task(self):
        """Start background task for cleaning stale presence."""
        if self._cleanup_task and not self._cleanup_task.done():
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Presence cleanup task started")

    async def _cleanup_loop(self):
        """Background loop for cleaning stale presence records."""
        while True:
            try:
                await asyncio.sleep(settings.PRESENCE_CLEANUP_INTERVAL)

                async with AsyncSessionLocal() as db:
                    # Get presence before cleanup
                    old_presence = await self.presence_service.get_all_rooms_presence_with_names(db)

                    # Cleanup stale records
                    cleaned = await self.presence_service.cleanup_stale_presence(db)
                    await db.commit()

                    if cleaned > 0:
                        # Get updated presence
                        new_presence = await self.presence_service.get_all_rooms_presence_with_names(db)

                        # Find rooms with changes and broadcast
                        for room_data in new_presence:
                            room_id = room_data["room_id"]
                            guest_count = self._get_active_guests_count(room_id)
                            total_people = room_data["total_count"] + guest_count
                            
                            message = {
                                "type": "presence_update",
                                "room_id": room_id,
                                "room_name": room_data["room_name"],
                                "occupants": room_data["occupants"],
                                "total_count": room_data["total_count"],
                                "guest_count": guest_count,
                                "total_people": total_people,
                                "timestamp": datetime.now().isoformat()
                            }
                            await self.broadcast_to_room(room_id, message)
                            await self.broadcast_all_presence(message)

                        logger.info(f"Cleaned {cleaned} stale presence records")

            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def stop_cleanup_task(self):
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


# Import here to avoid circular import
from sqlalchemy import select

# Global manager
room_manager = RoomConnectionManager()


# ==================== WebSocket Endpoints ====================

# IMPORTANT: Static routes must come BEFORE parameterized routes!
# "/ws/rooms/all/presence" must be defined before "/ws/rooms/{room_id}/presence"
# otherwise "all" will be captured as room_id parameter

@router.websocket("/ws/rooms/all/presence")
async def all_rooms_presence(websocket: WebSocket):
    """Subscribe to presence updates for ALL rooms (dashboard view)."""
    # WebSocket'ni darhol accept qilish - 403 xatosini oldini olish uchun
    await websocket.accept()
    room_manager.all_presence_subscribers.add(websocket)
    logger.info(f"WebSocket subscribed to all presence. Total: {len(room_manager.all_presence_subscribers)}")

    # Start cleanup task if not running
    await room_manager.start_cleanup_task()

    try:
        # Send initial presence for all rooms
        async with AsyncSessionLocal() as db:
            all_presence = await room_manager.presence_service.get_all_rooms_presence_with_names(db)
            
            # Add guest counts
            for room_data in all_presence:
                room_id = room_data["room_id"]
                guest_count = room_manager._get_active_guests_count(room_id)
                room_data["guest_count"] = guest_count
                room_data["total_people"] = room_data["total_count"] + guest_count
            
            total_students = sum(r["total_count"] for r in all_presence)
            total_guests = sum(r["guest_count"] for r in all_presence)
            total_people = total_students + total_guests

            await websocket.send_json({
                "type": "initial_all_presence",
                "rooms": all_presence,
                "total_students": total_students,
                "total_guests": total_guests,
                "total_people": total_people,
                "timestamp": datetime.now().isoformat()
            })

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif message.get("type") == "refresh":
                    # Client requesting refresh
                    async with AsyncSessionLocal() as db:
                        all_presence = await room_manager.presence_service.get_all_rooms_presence_with_names(db)
                        total_people = sum(r["total_count"] for r in all_presence)

                        await websocket.send_json({
                            "type": "all_presence_refresh",
                            "rooms": all_presence,
                            "total_people": total_people,
                            "timestamp": datetime.now().isoformat()
                        })

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"All presence WebSocket error: {e}")
                break

    finally:
        room_manager.unsubscribe_all_presence(websocket)


@router.websocket("/ws/rooms/{room_id}/presence")
async def room_presence_stream(websocket: WebSocket, room_id: int):
    """Subscribe to real-time presence updates for a specific room."""
    # WebSocket'ni darhol accept qilish
    await websocket.accept()
    room_manager.room_subscriptions[room_id].add(websocket)
    logger.info(f"WebSocket subscribed to room {room_id}. Total: {len(room_manager.room_subscriptions[room_id])}")

    # Start cleanup task if not running
    await room_manager.start_cleanup_task()

    try:
        # Send initial presence data
        async with AsyncSessionLocal() as db:
            room = await room_manager.room_service.get_room(db, room_id)
            if not room:
                await websocket.send_json({"type": "error", "message": "Room not found"})
                return

            presence_list = await room_manager.presence_service.get_room_presence(db, room_id)
            guest_count = room_manager._get_active_guests_count(room_id)
            total_people = len(presence_list) + guest_count

            await websocket.send_json({
                "type": "initial_presence",
                "room_id": room_id,
                "room_name": room.name,
                "occupants": [p.to_dict() for p in presence_list],
                "total_count": len(presence_list),
                "guest_count": guest_count,
                "total_people": total_people,
                "timestamp": datetime.now().isoformat()
            })

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Room presence WebSocket error: {e}")
                break

    finally:
        room_manager.unsubscribe_room(websocket, room_id)


@router.websocket("/ws/cameras/{camera_id}/stream")
async def camera_stream(websocket: WebSocket, camera_id: int):
    """Subscribe to video stream from a specific camera."""
    # WebSocket'ni darhol accept qilish
    await websocket.accept()
    room_manager.camera_subscriptions[camera_id].add(websocket)
    logger.info(f"WebSocket subscribed to camera {camera_id}. Total: {len(room_manager.camera_subscriptions[camera_id])}")

    try:
        # Send initial status
        status = room_manager.rtsp_manager.get_camera_status(camera_id)
        await websocket.send_json({
            "type": "status",
            "camera_id": camera_id,
            "connected": status.get("connected", False) if status else False,
            "running": status.get("running", False) if status else False,
            "fps": status.get("fps", 0) if status else 0
        })

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Camera stream WebSocket error: {e}")
                break

    finally:
        room_manager.unsubscribe_camera(websocket, camera_id)


# Function to get the manager (for use in other modules)
def get_room_manager() -> RoomConnectionManager:
    return room_manager
