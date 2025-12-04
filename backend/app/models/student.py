from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    group_name = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    
    def __repr__(self):
        return f"<Student(id={self.id}, student_id={self.student_id}, name={self.first_name} {self.last_name})>"

