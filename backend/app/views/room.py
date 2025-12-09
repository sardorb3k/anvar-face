from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ==================== Room Schemas ====================

class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class RoomResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    camera_count: int = 0

    class Config:
        from_attributes = True


class RoomDetailResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    cameras: List["CameraResponse"] = []

    class Config:
        from_attributes = True


# ==================== Camera Schemas ====================

class CameraCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rtsp_url: str = Field(..., min_length=1, max_length=500)


class CameraUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rtsp_url: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None


class CameraResponse(BaseModel):
    id: int
    room_id: int
    name: str
    rtsp_url: str
    is_active: bool
    created_at: datetime
    status: str = "disconnected"  # connected, streaming, disconnected

    class Config:
        from_attributes = True


class CameraStatusResponse(BaseModel):
    camera_id: int
    room_id: int
    connected: bool
    running: bool
    rtsp_url: str
    fps: int = 0


# ==================== Presence Schemas ====================

class OccupantInfo(BaseModel):
    student_id: int
    student_number: str
    first_name: str
    last_name: str
    group_name: Optional[str]
    last_seen_at: datetime
    confidence: float
    camera_id: Optional[int] = None


class RoomPresenceResponse(BaseModel):
    room_id: int
    room_name: str
    occupants: List[OccupantInfo]
    total_count: int


class AllRoomsPresenceResponse(BaseModel):
    rooms: List[RoomPresenceResponse]
    total_people: int


class StudentLocationResponse(BaseModel):
    found: bool
    room_id: Optional[int] = None
    room_name: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    confidence: Optional[float] = None
    camera_id: Optional[int] = None


class PresenceStatsResponse(BaseModel):
    total_people_tracked: int
    total_rooms: int
    occupied_rooms: int
    presence_timeout_seconds: int


# ==================== Control Schemas ====================

class CameraControlRequest(BaseModel):
    timeout: int = Field(default=30, ge=5, le=120)


class CameraControlResponse(BaseModel):
    success: bool
    message: str
    camera_id: int
    status: Optional[CameraStatusResponse] = None


# Update forward references
RoomDetailResponse.model_rebuild()
