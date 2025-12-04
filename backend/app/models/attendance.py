from sqlalchemy import Column, Integer, String, Date, Time, Float, TIMESTAMP, ForeignKey, UniqueConstraint, func
from app.core.database import Base


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_date = Column(Date, nullable=False, index=True)
    check_in_time = Column(Time, nullable=False)
    confidence_score = Column(Float, nullable=False)
    snapshot_path = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('student_id', 'attendance_date', name='unique_student_attendance_per_day'),
    )
    
    def __repr__(self):
        return f"<Attendance(id={self.id}, student_id={self.student_id}, date={self.attendance_date})>"

