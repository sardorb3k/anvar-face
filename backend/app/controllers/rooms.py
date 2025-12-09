from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.room import Room
from app.models.camera import Camera
from app.models.student import Student
from app.views.room import (
    RoomCreate, RoomUpdate, RoomResponse, RoomDetailResponse,
    CameraCreate, CameraUpdate, CameraResponse, CameraStatusResponse,
    RoomPresenceResponse, AllRoomsPresenceResponse, StudentLocationResponse,
    PresenceStatsResponse, CameraControlRequest, CameraControlResponse,
    OccupantInfo
)
from app.services.room_service import get_room_service
from app.services.presence_service import get_presence_service
from app.services.multi_rtsp_service import get_multi_rtsp_manager

router = APIRouter()


# ==================== Room CRUD ====================

@router.post("/", response_model=RoomResponse)
async def create_room(
    request: RoomCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new room."""
    room_service = get_room_service()

    # Check if name exists
    existing = await room_service.get_room_by_name(db, request.name)
    if existing:
        raise HTTPException(status_code=400, detail="Room name already exists")

    room = await room_service.create_room(db, request.name)
    return RoomResponse(
        id=room.id,
        name=room.name,
        is_active=room.is_active,
        created_at=room.created_at,
        camera_count=0
    )


@router.get("/", response_model=List[RoomResponse])
async def list_rooms(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all rooms."""
    room_service = get_room_service()
    rooms = await room_service.get_all_rooms(db, include_inactive)

    return [
        RoomResponse(
            id=room.id,
            name=room.name,
            is_active=room.is_active,
            created_at=room.created_at,
            camera_count=len(room.cameras) if room.cameras else 0
        )
        for room in rooms
    ]


@router.get("/{room_id}", response_model=RoomDetailResponse)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get room by ID with cameras."""
    room_service = get_room_service()
    room = await room_service.get_room(db, room_id)

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Get camera statuses
    rtsp_manager = get_multi_rtsp_manager()
    camera_statuses = rtsp_manager.get_room_cameras(room_id)

    cameras = []
    for camera in room.cameras:
        status = "disconnected"
        if camera.id in camera_statuses:
            cam_status = camera_statuses[camera.id]
            if cam_status.get("running"):
                status = "streaming"
            elif cam_status.get("connected"):
                status = "connected"

        cameras.append(CameraResponse(
            id=camera.id,
            room_id=camera.room_id,
            name=camera.name,
            rtsp_url=camera.rtsp_url,
            is_active=camera.is_active,
            created_at=camera.created_at,
            status=status
        ))

    return RoomDetailResponse(
        id=room.id,
        name=room.name,
        is_active=room.is_active,
        created_at=room.created_at,
        cameras=cameras
    )


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    request: RoomUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update room."""
    room_service = get_room_service()

    # Check name uniqueness if updating
    if request.name:
        existing = await room_service.get_room_by_name(db, request.name)
        if existing and existing.id != room_id:
            raise HTTPException(status_code=400, detail="Room name already exists")

    room = await room_service.update_room(
        db, room_id,
        name=request.name,
        is_active=request.is_active
    )

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    camera_count = await room_service.get_camera_count(db, room_id)

    return RoomResponse(
        id=room.id,
        name=room.name,
        is_active=room.is_active,
        created_at=room.created_at,
        camera_count=camera_count
    )


@router.delete("/{room_id}")
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete room and all its cameras."""
    room_service = get_room_service()
    rtsp_manager = get_multi_rtsp_manager()

    # Stop all cameras in room first
    rtsp_manager.stop_room_cameras(room_id)

    success = await room_service.delete_room(db, room_id)
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")

    return {"status": "success", "message": f"Room {room_id} deleted"}


# ==================== Camera CRUD ====================

@router.post("/{room_id}/cameras", response_model=CameraResponse)
async def add_camera(
    room_id: int,
    request: CameraCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a camera to a room."""
    room_service = get_room_service()

    camera = await room_service.add_camera(
        db, room_id,
        name=request.name,
        rtsp_url=request.rtsp_url
    )

    if not camera:
        raise HTTPException(
            status_code=400,
            detail="Failed to add camera. Room not found or camera limit reached."
        )

    return CameraResponse(
        id=camera.id,
        room_id=camera.room_id,
        name=camera.name,
        rtsp_url=camera.rtsp_url,
        is_active=camera.is_active,
        created_at=camera.created_at,
        status="disconnected"
    )


@router.get("/{room_id}/cameras", response_model=List[CameraResponse])
async def list_cameras(
    room_id: int,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all cameras in a room."""
    room_service = get_room_service()
    rtsp_manager = get_multi_rtsp_manager()

    cameras = await room_service.get_cameras_by_room(db, room_id, include_inactive)
    camera_statuses = rtsp_manager.get_room_cameras(room_id)

    result = []
    for camera in cameras:
        status = "disconnected"
        if camera.id in camera_statuses:
            cam_status = camera_statuses[camera.id]
            if cam_status.get("running"):
                status = "streaming"
            elif cam_status.get("connected"):
                status = "connected"

        result.append(CameraResponse(
            id=camera.id,
            room_id=camera.room_id,
            name=camera.name,
            rtsp_url=camera.rtsp_url,
            is_active=camera.is_active,
            created_at=camera.created_at,
            status=status
        ))

    return result


@router.put("/{room_id}/cameras/{camera_id}", response_model=CameraResponse)
async def update_camera(
    room_id: int,
    camera_id: int,
    request: CameraUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update camera."""
    room_service = get_room_service()
    rtsp_manager = get_multi_rtsp_manager()

    camera = await room_service.update_camera(
        db, camera_id,
        name=request.name,
        rtsp_url=request.rtsp_url,
        is_active=request.is_active
    )

    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    if camera.room_id != room_id:
        raise HTTPException(status_code=400, detail="Camera does not belong to this room")

    # Get status
    status = "disconnected"
    cam_status = rtsp_manager.get_camera_status(camera_id)
    if cam_status:
        if cam_status.get("running"):
            status = "streaming"
        elif cam_status.get("connected"):
            status = "connected"

    return CameraResponse(
        id=camera.id,
        room_id=camera.room_id,
        name=camera.name,
        rtsp_url=camera.rtsp_url,
        is_active=camera.is_active,
        created_at=camera.created_at,
        status=status
    )


@router.delete("/{room_id}/cameras/{camera_id}")
async def delete_camera(
    room_id: int,
    camera_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete camera."""
    room_service = get_room_service()
    rtsp_manager = get_multi_rtsp_manager()

    # Get camera to verify room
    camera = await room_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    if camera.room_id != room_id:
        raise HTTPException(status_code=400, detail="Camera does not belong to this room")

    # Stop camera if running
    rtsp_manager.stop_camera(camera_id)

    success = await room_service.delete_camera(db, camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")

    return {"status": "success", "message": f"Camera {camera_id} deleted"}


# ==================== Camera Control ====================

@router.post("/{room_id}/cameras/{camera_id}/start", response_model=CameraControlResponse)
async def start_camera(
    room_id: int,
    camera_id: int,
    request: CameraControlRequest = CameraControlRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Start streaming from a camera."""
    # Import here to avoid circular import
    from app.controllers.room_websocket import get_room_manager

    room_service = get_room_service()
    rtsp_manager = get_multi_rtsp_manager()
    room_manager = get_room_manager()

    camera = await room_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    if camera.room_id != room_id:
        raise HTTPException(status_code=400, detail="Camera does not belong to this room")

    if not camera.is_active:
        raise HTTPException(status_code=400, detail="Camera is disabled")

    # Start camera with WebSocket callback for frame broadcasting
    success = await room_manager.start_camera_with_callback(
        camera_id=camera.id,
        rtsp_url=camera.rtsp_url,
        room_id=room_id,
        timeout=request.timeout
    )

    if not success:
        return CameraControlResponse(
            success=False,
            message="Failed to start camera. Check RTSP URL or max streams limit.",
            camera_id=camera_id
        )

    status = rtsp_manager.get_camera_status(camera_id)

    return CameraControlResponse(
        success=True,
        message="Camera started successfully",
        camera_id=camera_id,
        status=CameraStatusResponse(
            camera_id=camera_id,
            room_id=room_id,
            connected=status.get("connected", False) if status else False,
            running=status.get("running", False) if status else False,
            rtsp_url=camera.rtsp_url,
            fps=status.get("fps", 0) if status else 0
        )
    )


@router.post("/{room_id}/cameras/{camera_id}/stop", response_model=CameraControlResponse)
async def stop_camera(
    room_id: int,
    camera_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Stop streaming from a camera."""
    room_service = get_room_service()
    rtsp_manager = get_multi_rtsp_manager()

    camera = await room_service.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    if camera.room_id != room_id:
        raise HTTPException(status_code=400, detail="Camera does not belong to this room")

    success = rtsp_manager.stop_camera(camera_id)

    return CameraControlResponse(
        success=success,
        message="Camera stopped" if success else "Camera was not running",
        camera_id=camera_id
    )


@router.post("/{room_id}/start-all")
async def start_all_cameras(
    room_id: int,
    request: CameraControlRequest = CameraControlRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Start all cameras in a room."""
    # Import here to avoid circular import
    from app.controllers.room_websocket import get_room_manager

    room_service = get_room_service()
    room_manager = get_room_manager()

    room = await room_service.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    cameras = await room_service.get_cameras_by_room(db, room_id)

    started = 0
    failed = 0

    for camera in cameras:
        if camera.is_active:
            # Start camera with WebSocket callback for frame broadcasting
            success = await room_manager.start_camera_with_callback(
                camera_id=camera.id,
                rtsp_url=camera.rtsp_url,
                room_id=room_id,
                timeout=request.timeout
            )
            if success:
                started += 1
            else:
                failed += 1

    return {
        "status": "success",
        "message": f"Started {started} cameras, {failed} failed",
        "started": started,
        "failed": failed
    }


@router.post("/{room_id}/stop-all")
async def stop_all_cameras(room_id: int):
    """Stop all cameras in a room."""
    rtsp_manager = get_multi_rtsp_manager()
    stopped = rtsp_manager.stop_room_cameras(room_id)

    return {
        "status": "success",
        "message": f"Stopped {stopped} cameras",
        "stopped": stopped
    }


# ==================== Presence Endpoints ====================

@router.get("/{room_id}/presence", response_model=RoomPresenceResponse)
async def get_room_presence(
    room_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get current presence in a room."""
    room_service = get_room_service()
    presence_service = get_presence_service()

    room = await room_service.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    presence_list = await presence_service.get_room_presence(db, room_id)

    return RoomPresenceResponse(
        room_id=room.id,
        room_name=room.name,
        occupants=[
            OccupantInfo(
                student_id=p.student_id,
                student_number=p.student_number,
                first_name=p.first_name,
                last_name=p.last_name,
                group_name=p.group_name,
                last_seen_at=p.last_seen_at,
                confidence=p.confidence,
                camera_id=p.camera_id
            )
            for p in presence_list
        ],
        total_count=len(presence_list)
    )


@router.get("/presence/all", response_model=AllRoomsPresenceResponse)
async def get_all_rooms_presence(
    db: AsyncSession = Depends(get_db)
):
    """Get presence for all rooms."""
    presence_service = get_presence_service()
    rooms_data = await presence_service.get_all_rooms_presence_with_names(db)

    total_people = sum(r["total_count"] for r in rooms_data)

    return AllRoomsPresenceResponse(
        rooms=[
            RoomPresenceResponse(
                room_id=r["room_id"],
                room_name=r["room_name"],
                occupants=[
                    OccupantInfo(**o) for o in r["occupants"]
                ],
                total_count=r["total_count"]
            )
            for r in rooms_data
        ],
        total_people=total_people
    )


@router.get("/presence/student/{student_id}", response_model=StudentLocationResponse)
async def get_student_location(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get where a specific student is currently located."""
    presence_service = get_presence_service()

    # Get student by student_id (string)
    result = await db.execute(
        select(Student).where(Student.student_id == student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    location = await presence_service.get_student_location(db, student.id)

    if not location:
        return StudentLocationResponse(found=False)

    return StudentLocationResponse(
        found=True,
        room_id=location["room_id"],
        room_name=location["room_name"],
        last_seen_at=location["last_seen_at"],
        confidence=location["confidence"],
        camera_id=location["camera_id"]
    )


@router.get("/presence/stats", response_model=PresenceStatsResponse)
async def get_presence_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get overall presence statistics."""
    presence_service = get_presence_service()
    stats = await presence_service.get_presence_stats(db)

    return PresenceStatsResponse(**stats)
