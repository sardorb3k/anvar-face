from fastapi import APIRouter, HTTPException
from app.services.rtsp_service import get_rtsp_service
from app.controllers.websocket import manager
from app.views.rtsp import RTSPConnectRequest, RTSPConnectResponse, RTSPStatusResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/connect", response_model=RTSPConnectResponse)
async def connect_rtsp(request: RTSPConnectRequest):
    """
    Connect to RTSP stream.
    
    Args:
        request: RTSP connection request with URL and timeout
        
    Returns:
        Connection status and result
    """
    try:
        rtsp_service = get_rtsp_service()
        
        # Validate RTSP URL
        if not request.rtsp_url.startswith(('rtsp://', 'rtsps://')):
            raise HTTPException(
                status_code=400,
                detail="Invalid RTSP URL. Must start with rtsp:// or rtsps://"
            )
        
        # Connect to RTSP stream
        success = rtsp_service.connect(request.rtsp_url, timeout=request.timeout)
        
        if success:
            # Start streaming and recognition
            await manager.start_streaming()
            
            status = rtsp_service.get_status()
            return RTSPConnectResponse(
                success=True,
                message="RTSP stream connected successfully",
                status=RTSPStatusResponse(**status)
            )
        else:
            return RTSPConnectResponse(
                success=False,
                message="Failed to connect to RTSP stream. Please check URL and network connection.",
                status=None
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to RTSP: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error connecting to RTSP stream: {str(e)}"
        )


@router.post("/disconnect", response_model=RTSPConnectResponse)
async def disconnect_rtsp():
    """
    Disconnect from RTSP stream.
    
    Returns:
        Disconnection status
    """
    try:
        rtsp_service = get_rtsp_service()
        
        # Stop streaming
        manager.stop_streaming()
        
        # Disconnect
        rtsp_service.disconnect()
        
        return RTSPConnectResponse(
            success=True,
            message="RTSP stream disconnected successfully",
            status=RTSPStatusResponse(
                connected=False,
                running=False,
                rtsp_url=None,
                fps=0,
                frame_count=0
            )
        )
    
    except Exception as e:
        logger.error(f"Error disconnecting RTSP: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error disconnecting RTSP stream: {str(e)}"
        )


@router.get("/status", response_model=RTSPStatusResponse)
async def get_rtsp_status():
    """
    Get RTSP stream status.
    
    Returns:
        Current connection status
    """
    try:
        rtsp_service = get_rtsp_service()
        status = rtsp_service.get_status()
        return RTSPStatusResponse(**status)
    
    except Exception as e:
        logger.error(f"Error getting RTSP status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting RTSP status: {str(e)}"
        )


@router.get("/stream")
async def get_rtsp_stream_mjpeg():
    """
    Get RTSP stream as MJPEG (for direct browser viewing).
    Note: For real-time updates, use WebSocket endpoint instead.
    
    Returns:
        MJPEG stream
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    
    rtsp_service = get_rtsp_service()
    
    if not rtsp_service.is_connected:
        raise HTTPException(
            status_code=400,
            detail="RTSP stream not connected. Please connect first."
        )
    
    async def generate_frames():
        """Generate MJPEG frames from RTSP stream."""
        while rtsp_service.is_connected:
            frame = rtsp_service.get_frame()
            if frame is not None:
                # Encode as JPEG
                frame_bytes = rtsp_service.encode_frame_jpeg(frame)
                
                # MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                await asyncio.sleep(0.033)  # ~30 FPS
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

