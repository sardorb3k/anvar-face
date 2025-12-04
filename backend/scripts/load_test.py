"""
Load testing script for face recognition attendance system.
Tests performance with multiple students and concurrent requests.
"""

import asyncio
import time
import numpy as np
import cv2
import base64
from concurrent.futures import ThreadPoolExecutor
import requests
from typing import List


API_URL = "http://localhost:8000"


def create_dummy_face_image(student_id: int) -> str:
    """Create a dummy face image and return as base64."""
    # Create a simple colored image
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Add some distinguishing features (simple shapes)
    color = (student_id * 10 % 255, student_id * 20 % 255, student_id * 30 % 255)
    cv2.circle(img, (320, 240), 100, color, -1)
    
    # Encode to jpeg
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return f"data:image/jpeg;base64,{img_base64}"


def register_student(student_id: str, first_name: str, last_name: str) -> bool:
    """Register a student."""
    try:
        response = requests.post(
            f"{API_URL}/api/students/register",
            json={
                "student_id": student_id,
                "first_name": first_name,
                "last_name": last_name,
                "group_name": "TEST-01"
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to register {student_id}: {e}")
        return False


def upload_student_images(student_id: str, num_images: int = 5) -> bool:
    """Upload images for a student."""
    try:
        files = []
        for i in range(num_images):
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', img)
            files.append(('files', (f'image_{i}.jpg', buffer.tobytes(), 'image/jpeg')))
        
        response = requests.post(
            f"{API_URL}/api/students/{student_id}/upload-images",
            files=files
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to upload images for {student_id}: {e}")
        return False


def check_in_attendance(image_base64: str) -> tuple:
    """Check in attendance and measure response time."""
    start_time = time.time()
    try:
        response = requests.post(
            f"{API_URL}/api/attendance/check-in",
            json={"image": image_base64},
            timeout=10
        )
        elapsed = time.time() - start_time
        success = response.status_code == 200
        return success, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"Check-in failed: {e}")
        return False, elapsed


def load_test_registration(num_students: int = 100):
    """Test registration of multiple students."""
    print(f"\n{'='*60}")
    print(f"LOAD TEST: Registering {num_students} students")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(num_students):
            student_id = f"LOAD{i:04d}"
            future = executor.submit(register_student, student_id, f"Student{i}", f"Test{i}")
            futures.append(future)
        
        for future in futures:
            if future.result():
                success_count += 1
    
    elapsed = time.time() - start_time
    
    print(f"\nResults:")
    print(f"  Total students: {num_students}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {num_students - success_count}")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Average time per student: {elapsed/num_students:.3f}s")


def load_test_check_in(num_requests: int = 50):
    """Test concurrent check-in requests."""
    print(f"\n{'='*60}")
    print(f"LOAD TEST: {num_requests} concurrent check-in requests")
    print(f"{'='*60}\n")
    
    # Create dummy images
    images = [create_dummy_face_image(i) for i in range(num_requests)]
    
    start_time = time.time()
    response_times = []
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_in_attendance, img) for img in images]
        
        for future in futures:
            success, elapsed = future.result()
            if success:
                success_count += 1
            response_times.append(elapsed)
    
    total_time = time.time() - start_time
    avg_response = np.mean(response_times)
    max_response = np.max(response_times)
    min_response = np.min(response_times)
    
    print(f"\nResults:")
    print(f"  Total requests: {num_requests}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {num_requests - success_count}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Requests per second: {num_requests/total_time:.2f}")
    print(f"\nResponse times:")
    print(f"  Average: {avg_response:.3f}s")
    print(f"  Min: {min_response:.3f}s")
    print(f"  Max: {max_response:.3f}s")
    
    # Check if meets performance requirements
    if avg_response < 2.0:
        print(f"\n✓ Performance requirement met (< 2 seconds)")
    else:
        print(f"\n✗ Performance requirement NOT met (>= 2 seconds)")


def performance_benchmark():
    """Run comprehensive performance benchmark."""
    print(f"\n{'#'*60}")
    print(f"# FACE RECOGNITION ATTENDANCE SYSTEM - PERFORMANCE BENCHMARK")
    print(f"{'#'*60}")
    
    # Test 1: Registration performance
    load_test_registration(num_students=100)
    
    # Wait a bit
    time.sleep(2)
    
    # Test 2: Check-in performance
    load_test_check_in(num_requests=50)
    
    print(f"\n{'#'*60}")
    print(f"# BENCHMARK COMPLETE")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    # Check if API is running
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✓ API is running")
            performance_benchmark()
        else:
            print("✗ API is not responding correctly")
    except Exception as e:
        print(f"✗ Cannot connect to API: {e}")
        print(f"  Make sure the backend is running at {API_URL}")

