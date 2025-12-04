from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, JSON, func
from app.core.database import Base


class StudentImage(Base):
    __tablename__ = "student_images"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = Column(String, nullable=False)
    embedding_vector = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    def __repr__(self):
        return f"<StudentImage(id={self.id}, student_id={self.student_id})>"

