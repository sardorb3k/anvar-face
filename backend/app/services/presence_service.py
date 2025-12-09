import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload

from app.models.room_presence import RoomPresence
from app.models.room import Room
from app.models.student import Student
from app.core.config import settings

logger = logging.getLogger(__name__)


class PresenceInfo:
    """Presence information for a student."""

    def __init__(
        self,
        student_id: int,
        student_number: str,
        first_name: str,
        last_name: str,
        group_name: Optional[str],
        last_seen_at: datetime,
        confidence: float,
        camera_id: Optional[int] = None
    ):
        self.student_id = student_id
        self.student_number = student_number
        self.first_name = first_name
        self.last_name = last_name
        self.group_name = group_name
        self.last_seen_at = last_seen_at
        self.confidence = confidence
        self.camera_id = camera_id

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "student_number": self.student_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "group_name": self.group_name,
            "last_seen_at": self.last_seen_at.isoformat(),
            "confidence": self.confidence,
            "camera_id": self.camera_id
        }


class PresenceService:
    """Service for tracking real-time room presence."""

    def __init__(self):
        self.presence_timeout = settings.PRESENCE_TIMEOUT_SECONDS
        logger.info(f"PresenceService initialized (timeout: {self.presence_timeout}s)")

    async def update_presence(
        self,
        db: AsyncSession,
        student_db_id: int,
        room_id: int,
        camera_id: int,
        confidence: float
    ) -> Optional[RoomPresence]:
        """
        Update student's current room presence (UPSERT).
        Student can only be in one room at a time.
        """
        try:
            # Check if presence record exists for this student
            result = await db.execute(
                select(RoomPresence).where(RoomPresence.student_id == student_db_id)
            )
            presence = result.scalar_one_or_none()

            now = datetime.now()

            if presence:
                # Update existing record
                presence.room_id = room_id
                presence.camera_id = camera_id
                presence.last_seen_at = now
                presence.confidence_score = confidence
            else:
                # Create new record
                presence = RoomPresence(
                    student_id=student_db_id,
                    room_id=room_id,
                    camera_id=camera_id,
                    last_seen_at=now,
                    confidence_score=confidence
                )
                db.add(presence)

            await db.flush()
            await db.refresh(presence)

            logger.debug(
                f"Presence updated: Student {student_db_id} -> Room {room_id} "
                f"(Camera {camera_id}, Confidence: {confidence:.2f})"
            )
            return presence

        except Exception as e:
            logger.error(f"Error updating presence: {e}")
            return None

    async def get_room_presence(
        self,
        db: AsyncSession,
        room_id: int,
        include_stale: bool = False
    ) -> List[PresenceInfo]:
        """
        Get all students currently in a room.
        By default excludes stale entries (older than timeout).
        """
        cutoff_time = datetime.now() - timedelta(seconds=self.presence_timeout)

        query = (
            select(RoomPresence, Student)
            .join(Student, RoomPresence.student_id == Student.id)
            .where(RoomPresence.room_id == room_id)
        )

        if not include_stale:
            query = query.where(RoomPresence.last_seen_at >= cutoff_time)

        query = query.order_by(RoomPresence.last_seen_at.desc())

        result = await db.execute(query)
        rows = result.all()

        return [
            PresenceInfo(
                student_id=student.id,
                student_number=student.student_id,
                first_name=student.first_name,
                last_name=student.last_name,
                group_name=student.group_name,
                last_seen_at=presence.last_seen_at,
                confidence=presence.confidence_score or 0.0,
                camera_id=presence.camera_id
            )
            for presence, student in rows
        ]

    async def get_all_rooms_presence(
        self,
        db: AsyncSession
    ) -> Dict[int, List[PresenceInfo]]:
        """Get presence for all rooms."""
        cutoff_time = datetime.now() - timedelta(seconds=self.presence_timeout)

        # Get all active rooms
        rooms_result = await db.execute(
            select(Room).where(Room.is_active == True)
        )
        rooms = rooms_result.scalars().all()

        # Get presence for each room
        result = {}
        for room in rooms:
            presence_list = await self.get_room_presence(db, room.id)
            result[room.id] = presence_list

        return result

    async def get_all_rooms_presence_with_names(
        self,
        db: AsyncSession
    ) -> List[dict]:
        """Get presence for all rooms with room names."""
        cutoff_time = datetime.now() - timedelta(seconds=self.presence_timeout)

        # Get all active rooms
        rooms_result = await db.execute(
            select(Room).where(Room.is_active == True).order_by(Room.name)
        )
        rooms = rooms_result.scalars().all()

        result = []
        for room in rooms:
            presence_list = await self.get_room_presence(db, room.id)
            result.append({
                "room_id": room.id,
                "room_name": room.name,
                "occupants": [p.to_dict() for p in presence_list],
                "total_count": len(presence_list)
            })

        return result

    async def get_student_location(
        self,
        db: AsyncSession,
        student_db_id: int
    ) -> Optional[dict]:
        """Get where a specific student is currently located."""
        cutoff_time = datetime.now() - timedelta(seconds=self.presence_timeout)

        result = await db.execute(
            select(RoomPresence, Room)
            .join(Room, RoomPresence.room_id == Room.id)
            .where(
                and_(
                    RoomPresence.student_id == student_db_id,
                    RoomPresence.last_seen_at >= cutoff_time
                )
            )
        )
        row = result.first()

        if not row:
            return None

        presence, room = row
        return {
            "room_id": room.id,
            "room_name": room.name,
            "last_seen_at": presence.last_seen_at.isoformat(),
            "confidence": presence.confidence_score,
            "camera_id": presence.camera_id
        }

    async def cleanup_stale_presence(
        self,
        db: AsyncSession
    ) -> int:
        """
        Remove presence entries older than timeout.
        Returns count of removed entries.
        """
        cutoff_time = datetime.now() - timedelta(seconds=self.presence_timeout)

        # Get count before delete
        count_result = await db.execute(
            select(RoomPresence).where(RoomPresence.last_seen_at < cutoff_time)
        )
        stale_records = count_result.scalars().all()
        count = len(stale_records)

        if count > 0:
            await db.execute(
                delete(RoomPresence).where(RoomPresence.last_seen_at < cutoff_time)
            )
            await db.flush()
            logger.info(f"Cleaned up {count} stale presence records")

        return count

    async def clear_room_presence(
        self,
        db: AsyncSession,
        room_id: int
    ) -> int:
        """Clear all presence records for a room. Returns count cleared."""
        result = await db.execute(
            select(RoomPresence).where(RoomPresence.room_id == room_id)
        )
        records = result.scalars().all()
        count = len(records)

        if count > 0:
            await db.execute(
                delete(RoomPresence).where(RoomPresence.room_id == room_id)
            )
            await db.flush()
            logger.info(f"Cleared {count} presence records for room {room_id}")

        return count

    async def get_presence_stats(
        self,
        db: AsyncSession
    ) -> dict:
        """Get overall presence statistics."""
        cutoff_time = datetime.now() - timedelta(seconds=self.presence_timeout)

        # Count active presence records
        active_result = await db.execute(
            select(RoomPresence).where(RoomPresence.last_seen_at >= cutoff_time)
        )
        active_count = len(active_result.scalars().all())

        # Count total rooms
        rooms_result = await db.execute(
            select(Room).where(Room.is_active == True)
        )
        room_count = len(rooms_result.scalars().all())

        # Count rooms with people
        rooms_with_presence = await db.execute(
            select(RoomPresence.room_id)
            .where(RoomPresence.last_seen_at >= cutoff_time)
            .distinct()
        )
        occupied_rooms = len(rooms_with_presence.scalars().all())

        return {
            "total_people_tracked": active_count,
            "total_rooms": room_count,
            "occupied_rooms": occupied_rooms,
            "presence_timeout_seconds": self.presence_timeout
        }


# Global instance
_presence_service: Optional[PresenceService] = None


def get_presence_service() -> PresenceService:
    """Get or create global PresenceService instance."""
    global _presence_service
    if _presence_service is None:
        _presence_service = PresenceService()
    return _presence_service
