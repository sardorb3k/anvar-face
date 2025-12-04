from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
import base64
import cv2
import numpy as np
from datetime import date, time, datetime, timedelta
import os

from app.core.database import get_db
from app.models.student import Student
from app.models.attendance import Attendance
from app.views.attendance import AttendanceCheckIn, AttendanceResponse, AttendanceWithStudent
from app.services.face_service import get_face_service
from app.services.vector_service import get_vector_service
from app.core.config import settings

router = APIRouter()


@router.post("/check-in")
async def check_in_attendance(
    data: AttendanceCheckIn,
    db: AsyncSession = Depends(get_db)
):
    """
    Check in attendance using face recognition.
    
    Args:
        data: Base64 encoded image from camera
        
    Returns:
        Student information and attendance status
    """
    try:
        # Decode base64 image
        # Remove data URL prefix if present
        image_data = data.image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        # Get face service
        face_service = get_face_service()
        
        # Extract embedding
        embedding = face_service.extract_embedding(image)
        
        if embedding is None:
            return {
                "status": "error",
                "message": "Yuz topilmadi, qaytadan urining",
                "student": None
            }
        
        # Search in FAISS
        vector_service = get_vector_service()
        match = vector_service.search_with_threshold(embedding)
        
        if match is None:
            return {
                "status": "error",
                "message": "Talaba bazada yo'q",
                "student": None
            }
        
        student_db_id, confidence = match
        
        # Get student information
        result = await db.execute(
            select(Student).where(Student.id == student_db_id)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            return {
                "status": "error",
                "message": "Talaba ma'lumotlari topilmadi",
                "student": None
            }
        
        # Check if already attended today
        today = date.today()
        result = await db.execute(
            select(Attendance).where(
                and_(
                    Attendance.student_id == student.id,
                    Attendance.attendance_date == today
                )
            )
        )
        existing_attendance = result.scalar_one_or_none()
        
        if existing_attendance:
            return {
                "status": "already_attended",
                "message": "Siz allaqachon davomat qilgansiz",
                "student": {
                    "id": student.id,
                    "student_id": student.student_id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "group_name": student.group_name
                },
                "confidence": confidence,
                "check_in_time": existing_attendance.check_in_time.isoformat()
            }
        
        # Save snapshot
        snapshot_dir = os.path.join(settings.IMAGES_BASE_PATH, "attendance")
        os.makedirs(snapshot_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = f"{student.student_id}_{timestamp}.jpg"
        snapshot_path = os.path.join(snapshot_dir, snapshot_filename)
        cv2.imwrite(snapshot_path, image)
        
        # Create attendance record
        now = datetime.now()
        attendance = Attendance(
            student_id=student.id,
            attendance_date=today,
            check_in_time=now.time(),
            confidence_score=confidence,
            snapshot_path=snapshot_path
        )
        
        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
        
        return {
            "status": "success",
            "message": "Davomat muvaffaqiyatli qabul qilindi",
            "student": {
                "id": student.id,
                "student_id": student.student_id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "group_name": student.group_name
            },
            "confidence": confidence,
            "check_in_time": attendance.check_in_time.isoformat(),
            "attendance_id": attendance.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("/today")
async def get_today_attendance(
    db: AsyncSession = Depends(get_db)
):
    """Get today's attendance records with student information."""
    today = date.today()
    
    # Join attendance with students
    result = await db.execute(
        select(
            Attendance.id,
            Attendance.student_id,
            Student.student_id.label('student_number'),
            Student.first_name,
            Student.last_name,
            Student.group_name,
            Attendance.attendance_date,
            Attendance.check_in_time,
            Attendance.confidence_score,
            Attendance.snapshot_path
        )
        .join(Student, Attendance.student_id == Student.id)
        .where(Attendance.attendance_date == today)
        .order_by(Attendance.check_in_time.desc())
    )
    
    records = result.all()
    
    attendance_list = []
    for record in records:
        attendance_list.append({
            "id": record.id,
            "student_id": record.student_id,
            "student_number": record.student_number,
            "first_name": record.first_name,
            "last_name": record.last_name,
            "group_name": record.group_name,
            "attendance_date": record.attendance_date.isoformat(),
            "check_in_time": record.check_in_time.isoformat(),
            "confidence_score": record.confidence_score,
            "snapshot_path": record.snapshot_path
        })
    
    return {
        "date": today.isoformat(),
        "total_attendance": len(attendance_list),
        "records": attendance_list
    }


@router.get("/student/{student_id}")
async def get_student_attendance(
    student_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get attendance history for a specific student.
    
    Args:
        student_id: Student's ID
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
    """
    # Get student
    result = await db.execute(
        select(Student).where(Student.student_id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Build query
    query = select(Attendance).where(Attendance.student_id == student.id)
    
    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.where(Attendance.attendance_date >= from_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.where(Attendance.attendance_date <= to_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
    
    # Execute query
    query = query.order_by(Attendance.attendance_date.desc())
    result = await db.execute(query)
    records = result.scalars().all()
    
    attendance_list = []
    for record in records:
        attendance_list.append({
            "id": record.id,
            "attendance_date": record.attendance_date.isoformat(),
            "check_in_time": record.check_in_time.isoformat(),
            "confidence_score": record.confidence_score,
            "snapshot_path": record.snapshot_path
        })
    
    return {
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "group_name": student.group_name
        },
        "total_records": len(attendance_list),
        "records": attendance_list
    }


@router.get("/statistics")
async def get_attendance_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Get attendance statistics."""
    today = date.today()
    
    # Total students
    total_students_result = await db.execute(select(func.count(Student.id)))
    total_students = total_students_result.scalar()
    
    # Today's attendance
    today_attendance_result = await db.execute(
        select(func.count(Attendance.id)).where(Attendance.attendance_date == today)
    )
    today_attendance = today_attendance_result.scalar()
    
    # This week's attendance
    week_start = today - timedelta(days=today.weekday())
    week_attendance_result = await db.execute(
        select(func.count(Attendance.id)).where(Attendance.attendance_date >= week_start)
    )
    week_attendance = week_attendance_result.scalar()
    
    # This month's attendance
    month_start = today.replace(day=1)
    month_attendance_result = await db.execute(
        select(func.count(Attendance.id)).where(Attendance.attendance_date >= month_start)
    )
    month_attendance = month_attendance_result.scalar()
    
    # Attendance rate
    attendance_rate = (today_attendance / total_students * 100) if total_students > 0 else 0
    
    return {
        "total_students": total_students,
        "today_attendance": today_attendance,
        "week_attendance": week_attendance,
        "month_attendance": month_attendance,
        "attendance_rate": round(attendance_rate, 2),
        "date": today.isoformat()
    }

