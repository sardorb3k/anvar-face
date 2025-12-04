"""
GPU performance test script - tests GPU utilization and performance.
"""
import sys
import os
import time
import logging
import numpy as np
import cv2

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.face_service import get_face_service
from app.services.vector_service import get_vector_service
from app.services.gpu_monitor import get_gpu_monitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_image(width=640, height=480):
    """Create a test image with a synthetic face-like pattern."""
    # Create a simple test image
    image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    # Add a simple face-like circle
    center = (width // 2, height // 2)
    cv2.circle(image, center, min(width, height) // 4, (200, 180, 160), -1)
    cv2.circle(image, (center[0] - 40, center[1] - 20), 10, (0, 0, 0), -1)  # Left eye
    cv2.circle(image, (center[0] + 40, center[1] - 20), 10, (0, 0, 0), -1)  # Right eye
    cv2.ellipse(image, (center[0], center[1] + 20), (30, 15), 0, 0, 180, (0, 0, 0), 2)  # Mouth
    return image


def test_face_service_gpu():
    """Test face service GPU performance."""
    logger.info("\n" + "=" * 70)
    logger.info("Face Service GPU Performance Test")
    logger.info("=" * 70)
    
    try:
        face_service = get_face_service()
        
        # Create test images
        num_images = 10
        logger.info(f"Creating {num_images} test images...")
        test_images = [create_test_image() for _ in range(num_images)]
        
        # Test single image processing
        logger.info("\nTesting single image processing...")
        start_time = time.time()
        for i, image in enumerate(test_images[:3]):
            embedding = face_service.extract_embedding(image)
            if embedding is not None:
                logger.info(f"  Image {i+1}: ✓ Embedding extracted (shape: {embedding.shape})")
            else:
                logger.warning(f"  Image {i+1}: ✗ No face detected")
        single_time = time.time() - start_time
        logger.info(f"Single image processing time: {single_time:.2f}s ({single_time/3:.3f}s per image)")
        
        # Test batch processing
        logger.info("\nTesting batch processing...")
        start_time = time.time()
        embeddings = face_service.extract_embeddings_batch(test_images, batch_size=8)
        batch_time = time.time() - start_time
        successful = sum(1 for e in embeddings if e is not None)
        logger.info(f"Batch processing time: {batch_time:.2f}s ({batch_time/num_images:.3f}s per image)")
        logger.info(f"Successful embeddings: {successful}/{num_images}")
        
        # Check GPU status
        logger.info("\nGPU Status after processing:")
        gpu_monitor = get_gpu_monitor()
        gpu_monitor.log_gpu_status()
        
        logger.info("\n✓ Face service GPU test completed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Face service GPU test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_service_gpu():
    """Test vector service GPU performance."""
    logger.info("\n" + "=" * 70)
    logger.info("Vector Service GPU Performance Test")
    logger.info("=" * 70)
    
    try:
        vector_service = get_vector_service()
        
        # Get stats
        stats = vector_service.get_stats()
        logger.info(f"Vector Service Stats: {stats}")
        
        # Create test embeddings
        num_embeddings = 100
        dimension = stats['dimension']
        logger.info(f"Creating {num_embeddings} test embeddings (dimension: {dimension})...")
        
        test_embeddings = []
        for i in range(num_embeddings):
            # Create random normalized embedding
            embedding = np.random.randn(dimension).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            test_embeddings.append(embedding)
        
        # Test batch add
        logger.info("\nTesting batch add to index...")
        start_time = time.time()
        student_ids = list(range(1, num_embeddings + 1))
        vector_service.add_embeddings_batch(test_embeddings, student_ids)
        add_time = time.time() - start_time
        logger.info(f"Batch add time: {add_time:.2f}s ({add_time/num_embeddings*1000:.2f}ms per embedding)")
        
        # Test search
        logger.info("\nTesting search performance...")
        query_embedding = test_embeddings[0]
        num_searches = 100
        start_time = time.time()
        for _ in range(num_searches):
            results = vector_service.search(query_embedding, k=5)
        search_time = time.time() - start_time
        logger.info(f"Search time for {num_searches} queries: {search_time:.2f}s "
                   f"({search_time/num_searches*1000:.2f}ms per query)")
        
        # Check GPU status
        logger.info("\nGPU Status after processing:")
        gpu_monitor = get_gpu_monitor()
        gpu_monitor.log_gpu_status()
        
        logger.info("\n✓ Vector service GPU test completed!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Vector service GPU test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    logger.info("\n" + "=" * 70)
    logger.info("GPU Performance Test Suite")
    logger.info("=" * 70)
    
    # Check GPU availability
    gpu_monitor = get_gpu_monitor()
    logger.info("\nInitial GPU Status:")
    gpu_monitor.log_gpu_status()
    
    # Run tests
    results = []
    
    results.append(("Face Service", test_face_service_gpu()))
    results.append(("Vector Service", test_vector_service_gpu()))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Test Summary")
    logger.info("=" * 70)
    
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    logger.info("\n" + "=" * 70)
    logger.info(f"Overall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    logger.info("=" * 70)
    
    logger.info("\nFinal GPU Status:")
    gpu_monitor.log_gpu_status()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

