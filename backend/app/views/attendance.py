from pydantic import BaseModel, Field
from datetime import date, time, datetime
from typing import Optional


class AttendanceCheckIn(BaseModel):
    image: str = Field(..., description="Base64 encoded image")


class AttendanceCreate(BaseModel):
    student_id: int
    attendance_date: date
    check_in_time: time
    confidence_score: float
    snapshot_path: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    attendance_date: date
    check_in_time: time
    confidence_score: float
    snapshot_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AttendanceWithStudent(BaseModel):
    id: int
    student_id: int
    student_number: str
    first_name: str
    last_name: str
    group_name: Optional[str]
    attendance_date: date
    check_in_time: time
    confidence_score: float
    snapshot_path: Optional[str]

