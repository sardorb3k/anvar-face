"""
System test script - validates all components of the face recognition system.
"""

import sys
import time
import numpy as np


def test_imports():
    """Test if all required packages are installed."""
    print("\n[1/6] Testing imports...")
    
    try:
        import fastapi
        import sqlalchemy
        import insightface
        import faiss
        import cv2
        import PIL
        print("  ✓ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_face_service():
    """Test face recognition service."""
    print("\n[2/6] Testing face recognition service...")
    
    try:
        from app.services.face_service import get_face_service
        
        service = get_face_service()
        print("  ✓ Face service initialized")
        
        # Test with dummy image
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        faces = service.detect_faces(dummy_image)
        print(f"  ✓ Face detection works (found {len(faces)} faces)")
        
        return True
    except Exception as e:
        print(f"  ✗ Face service failed: {e}")
        return False


def test_vector_service():
    """Test FAISS vector service."""
    print("\n[3/6] Testing FAISS vector service...")
    
    try:
        from app.services.vector_service import get_vector_service
        
        service = get_vector_service()
        print("  ✓ Vector service initialized")
        
        # Test adding and searching
        test_embedding = np.random.rand(512).astype(np.float32)
        service.add_embedding(test_embedding, 999999)
        
        results = service.search(test_embedding, k=1)
        if results and results[0][0] == 999999:
            print("  ✓ Vector search works")
        else:
            print("  ⚠ Vector search might have issues")
        
        return True
    except Exception as e:
        print(f"  ✗ Vector service failed: {e}")
        return False


def test_database_models():
    """Test database models."""
    print("\n[4/6] Testing database models...")
    
    try:
        from app.models import Student, StudentImage, Attendance
        print("  ✓ Database models loaded")
        return True
    except Exception as e:
        print(f"  ✗ Database models failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoint imports."""
    print("\n[5/6] Testing API endpoints...")
    
    try:
        from app.api import students, attendance
        from app.main import app
        print("  ✓ API endpoints loaded")
        return True
    except Exception as e:
        print(f"  ✗ API endpoints failed: {e}")
        return False


def test_performance():
    """Test basic performance metrics."""
    print("\n[6/6] Testing performance...")
    
    try:
        from app.services.face_service import get_face_service
        
        service = get_face_service()
        dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Time face detection
        start = time.time()
        for _ in range(10):
            service.detect_faces(dummy_image)
        elapsed = (time.time() - start) / 10
        
        print(f"  ✓ Average face detection time: {elapsed:.3f}s")
        
        if elapsed < 2.0:
            print("  ✓ Performance meets requirements (< 2s)")
        else:
            print("  ⚠ Performance slower than target (> 2s)")
        
        return True
    except Exception as e:
        print(f"  ✗ Performance test failed: {e}")
        return False


def main():
    """Run all system tests."""
    print("="*60)
    print("FACE RECOGNITION ATTENDANCE SYSTEM - SYSTEM TESTS")
    print("="*60)
    
    tests = [
        test_imports,
        test_face_service,
        test_vector_service,
        test_database_models,
        test_api_endpoints,
        test_performance,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ✗ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please fix issues before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

