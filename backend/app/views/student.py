from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StudentCreate(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    group_name: Optional[str] = Field(None, max_length=50)


class StudentResponse(BaseModel):
    id: int
    student_id: str
    first_name: str
    last_name: str
    group_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

