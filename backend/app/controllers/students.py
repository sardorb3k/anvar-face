from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import cv2
import numpy as np
from datetime import datetime
import base64

from app.core.database import get_db
from app.models.student import Student
from app.models.student_image import StudentImage
from app.views.student import StudentCreate, StudentResponse
from app.services.face_service import get_face_service
from app.services.vector_service import get_vector_service
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=StudentResponse)
async def register_student(
    student: StudentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new student.
    
    Args:
        student: Student data (student_id, first_name, last_name, group_name)
        
    Returns:
        Created student record
    """
    # Check if student_id already exists
    result = await db.execute(
        select(Student).where(Student.student_id == student.student_id)
    )
    existing_student = result.scalar_one_or_none()
    
    if existing_student:
        raise HTTPException(status_code=400, detail="Student ID already exists")
    
    # Create new student
    new_student = Student(
        student_id=student.student_id,
        first_name=student.first_name,
        last_name=student.last_name,
        group_name=student.group_name
    )
    
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    
    # Create student image directory
    student_dir = os.path.join(settings.IMAGES_BASE_PATH, student.student_id)
    os.makedirs(student_dir, exist_ok=True)
    
    return new_student


@router.post("/{student_id}/upload-images")
async def upload_student_images(
    student_id: str,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload multiple images for a student and extract face embeddings.
    
    Args:
        student_id: Student's ID
        files: List of image files (5-10 images recommended)
        
    Returns:
        Success message with statistics
    """
    # Validate number of images
    if len(files) < 5:
        raise HTTPException(status_code=400, detail="Please upload at least 5 images")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed")
    
    # Get student from database
    result = await db.execute(
        select(Student).where(Student.student_id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get services
    face_service = get_face_service()
    vector_service = get_vector_service()
    
    # Create directory for student images
    student_dir = os.path.join(settings.IMAGES_BASE_PATH, student_id)
    os.makedirs(student_dir, exist_ok=True)
    
    successful_uploads = 0
    failed_uploads = 0
    embeddings = []
    image_paths = []
    
    for i, file in enumerate(files):
        try:
            # Validate file type
            if not file.content_type.startswith('image/'):
                failed_uploads += 1
                continue
            
            # Read image
            contents = await file.read()
            
            # Validate file size (max 5MB)
            if len(contents) > 5 * 1024 * 1024:
                failed_uploads += 1
                continue
            
            # Convert to numpy array
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                failed_uploads += 1
                continue
            
            # Validate image quality
            is_valid, message = face_service.validate_image_quality(image)
            if not is_valid:
                failed_uploads += 1
                continue
            
            # Extract embedding
            embedding = face_service.extract_embedding(image)
            
            if embedding is None:
                failed_uploads += 1
                continue
            
            # Save image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{student_id}_{timestamp}_{i}.jpg"
            filepath = os.path.join(student_dir, filename)
            cv2.imwrite(filepath, image)
            
            embeddings.append(embedding)
            image_paths.append(filepath)
            successful_uploads += 1
            
        except Exception as e:
            failed_uploads += 1
            continue
    
    # Check if we have enough successful uploads
    if successful_uploads < 5:
        raise HTTPException(
            status_code=400,
            detail=f"Only {successful_uploads} valid images processed. At least 5 required."
        )
    
    # Save to database and FAISS
    student_db_ids = []
    for embedding, image_path in zip(embeddings, image_paths):
        # Save to database
        student_image = StudentImage(
            student_id=student.id,
            image_path=image_path,
            embedding_vector=embedding.tolist()
        )
        db.add(student_image)
        student_db_ids.append(student.id)
    
    await db.commit()
    
    # Add to FAISS index
    vector_service.add_embeddings_batch(embeddings, student_db_ids)
    
    return {
        "status": "success",
        "message": f"Successfully processed {successful_uploads} images",
        "successful_uploads": successful_uploads,
        "failed_uploads": failed_uploads,
        "student_id": student_id
    }


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get student by ID."""
    result = await db.execute(
        select(Student).where(Student.student_id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return student


@router.get("/", response_model=List[StudentResponse])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all students with pagination."""
    result = await db.execute(
        select(Student).offset(skip).limit(limit)
    )
    students = result.scalars().all()
    
    return students


@router.delete("/{student_id}")
async def delete_student(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a student and all their data."""
    # Get student
    result = await db.execute(
        select(Student).where(Student.student_id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Remove from FAISS
    vector_service = get_vector_service()
    vector_service.remove_student_embeddings(student.id)
    
    # Delete images from filesystem
    student_dir = os.path.join(settings.IMAGES_BASE_PATH, student_id)
    if os.path.exists(student_dir):
        import shutil
        shutil.rmtree(student_dir)
    
    # Delete from database (cascade will handle related records)
    await db.delete(student)
    await db.commit()
    
    return {"status": "success", "message": f"Student {student_id} deleted"}

