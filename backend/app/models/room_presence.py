from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class RoomPresence(Base):
    __tablename__ = "room_presence"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Bir student faqat bitta xonada bo'lishi mumkin
        index=True
    )
    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    camera_id = Column(
        Integer,
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True
    )
    last_seen_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    confidence_score = Column(Float, nullable=True)

    # Relationships
    student = relationship("Student")
    room = relationship("Room")
    camera = relationship("Camera")

    def __repr__(self):
        return f"<RoomPresence(student_id={self.student_id}, room_id={self.room_id}, last_seen={self.last_seen_at})>"
