import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.room import Room
from app.models.camera import Camera
from app.core.config import settings

logger = logging.getLogger(__name__)


class RoomService:
    """CRUD operations for rooms and cameras."""

    # ==================== Room Operations ====================

    async def create_room(
        self,
        db: AsyncSession,
        name: str
    ) -> Room:
        """Create a new room."""
        room = Room(name=name)
        db.add(room)
        await db.flush()
        await db.refresh(room)
        logger.info(f"Room created: {room.name} (ID: {room.id})")
        return room

    async def get_room(
        self,
        db: AsyncSession,
        room_id: int
    ) -> Optional[Room]:
        """Get room by ID with cameras."""
        result = await db.execute(
            select(Room)
            .options(selectinload(Room.cameras))
            .where(Room.id == room_id)
        )
        return result.scalar_one_or_none()

    async def get_room_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[Room]:
        """Get room by name."""
        result = await db.execute(
            select(Room).where(Room.name == name)
        )
        return result.scalar_one_or_none()

    async def get_all_rooms(
        self,
        db: AsyncSession,
        include_inactive: bool = False
    ) -> List[Room]:
        """Get all rooms with camera counts."""
        query = select(Room).options(selectinload(Room.cameras))
        if not include_inactive:
            query = query.where(Room.is_active == True)
        query = query.order_by(Room.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_room(
        self,
        db: AsyncSession,
        room_id: int,
        name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Room]:
        """Update room."""
        room = await self.get_room(db, room_id)
        if not room:
            return None

        if name is not None:
            room.name = name
        if is_active is not None:
            room.is_active = is_active

        await db.flush()
        await db.refresh(room)
        logger.info(f"Room updated: {room.name} (ID: {room.id})")
        return room

    async def delete_room(
        self,
        db: AsyncSession,
        room_id: int
    ) -> bool:
        """Delete room and all its cameras."""
        room = await self.get_room(db, room_id)
        if not room:
            return False

        await db.delete(room)
        await db.flush()
        logger.info(f"Room deleted: ID {room_id}")
        return True

    # ==================== Camera Operations ====================

    async def add_camera(
        self,
        db: AsyncSession,
        room_id: int,
        name: str,
        rtsp_url: str
    ) -> Optional[Camera]:
        """Add a camera to a room."""
        # Check room exists
        room = await self.get_room(db, room_id)
        if not room:
            logger.error(f"Room {room_id} not found")
            return None

        # Check camera limit
        camera_count = await self.get_camera_count(db, room_id)
        if camera_count >= settings.MAX_CAMERAS_PER_ROOM:
            logger.error(f"Room {room_id} has max cameras ({settings.MAX_CAMERAS_PER_ROOM})")
            return None

        camera = Camera(
            room_id=room_id,
            name=name,
            rtsp_url=rtsp_url
        )
        db.add(camera)
        await db.flush()
        await db.refresh(camera)
        logger.info(f"Camera added: {camera.name} (ID: {camera.id}) to Room {room_id}")
        return camera

    async def get_camera(
        self,
        db: AsyncSession,
        camera_id: int
    ) -> Optional[Camera]:
        """Get camera by ID."""
        result = await db.execute(
            select(Camera).where(Camera.id == camera_id)
        )
        return result.scalar_one_or_none()

    async def get_cameras_by_room(
        self,
        db: AsyncSession,
        room_id: int,
        include_inactive: bool = False
    ) -> List[Camera]:
        """Get all cameras in a room."""
        query = select(Camera).where(Camera.room_id == room_id)
        if not include_inactive:
            query = query.where(Camera.is_active == True)
        query = query.order_by(Camera.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_all_cameras(
        self,
        db: AsyncSession,
        include_inactive: bool = False
    ) -> List[Camera]:
        """Get all cameras."""
        query = select(Camera)
        if not include_inactive:
            query = query.where(Camera.is_active == True)
        query = query.order_by(Camera.room_id, Camera.name)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_camera_count(
        self,
        db: AsyncSession,
        room_id: int
    ) -> int:
        """Get camera count for a room."""
        result = await db.execute(
            select(func.count(Camera.id)).where(Camera.room_id == room_id)
        )
        return result.scalar() or 0

    async def update_camera(
        self,
        db: AsyncSession,
        camera_id: int,
        name: Optional[str] = None,
        rtsp_url: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Camera]:
        """Update camera."""
        camera = await self.get_camera(db, camera_id)
        if not camera:
            return None

        if name is not None:
            camera.name = name
        if rtsp_url is not None:
            camera.rtsp_url = rtsp_url
        if is_active is not None:
            camera.is_active = is_active

        await db.flush()
        await db.refresh(camera)
        logger.info(f"Camera updated: {camera.name} (ID: {camera.id})")
        return camera

    async def delete_camera(
        self,
        db: AsyncSession,
        camera_id: int
    ) -> bool:
        """Delete camera."""
        camera = await self.get_camera(db, camera_id)
        if not camera:
            return False

        await db.delete(camera)
        await db.flush()
        logger.info(f"Camera deleted: ID {camera_id}")
        return True


# Global instance
_room_service: Optional[RoomService] = None


def get_room_service() -> RoomService:
    """Get or create global RoomService instance."""
    global _room_service
    if _room_service is None:
        _room_service = RoomService()
    return _room_service
