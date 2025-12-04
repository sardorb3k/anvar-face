from pydantic import BaseModel, Field
from typing import Optional


class RTSPConnectRequest(BaseModel):
    rtsp_url: str = Field(..., description="RTSP stream URL (e.g., rtsp://user:pass@ip:port/stream)")
    timeout: int = Field(30, ge=5, le=120, description="Connection timeout in seconds")


class RTSPStatusResponse(BaseModel):
    connected: bool
    running: bool
    rtsp_url: Optional[str] = None
    fps: float = 0
    frame_count: int = 0


class RTSPConnectResponse(BaseModel):
    success: bool
    message: str
    status: Optional[RTSPStatusResponse] = None

