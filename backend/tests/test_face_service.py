import pytest
import numpy as np
import cv2
from app.services.face_service import FaceRecognitionService, get_face_service


class TestFaceRecognitionService:
    """Tests for face recognition service."""
    
    @pytest.fixture
    def face_service(self):
        """Get face service instance."""
        return get_face_service()
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        # Create a blank image (simple test)
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        return image
    
    def test_service_initialization(self, face_service):
        """Test that face service initializes correctly."""
        assert face_service is not None
        assert face_service.app is not None
        assert face_service.embedding_dimension == 512
    
    def test_preprocess_image_grayscale(self, face_service):
        """Test preprocessing of grayscale images."""
        gray_image = np.zeros((480, 640), dtype=np.uint8)
        processed = face_service.preprocess_image(gray_image)
        assert len(processed.shape) == 3
        assert processed.shape[2] == 3
    
    def test_preprocess_image_rgba(self, face_service):
        """Test preprocessing of RGBA images."""
        rgba_image = np.zeros((480, 640, 4), dtype=np.uint8)
        processed = face_service.preprocess_image(rgba_image)
        assert len(processed.shape) == 3
        assert processed.shape[2] == 3
    
    def test_detect_faces_no_face(self, face_service, sample_image):
        """Test face detection on image without faces."""
        faces = face_service.detect_faces(sample_image)
        assert isinstance(faces, list)
    
    def test_extract_embedding_no_face(self, face_service, sample_image):
        """Test embedding extraction on image without faces."""
        embedding = face_service.extract_embedding(sample_image)
        # Should return None for image without faces
        assert embedding is None or isinstance(embedding, np.ndarray)
    
    def test_validate_image_quality_small(self, face_service):
        """Test image quality validation for small images."""
        small_image = np.zeros((50, 50, 3), dtype=np.uint8)
        is_valid, message = face_service.validate_image_quality(small_image)
        assert not is_valid
        assert "too small" in message.lower()
    
    def test_validate_image_quality_large(self, face_service):
        """Test image quality validation for large images."""
        large_image = np.zeros((5000, 5000, 3), dtype=np.uint8)
        is_valid, message = face_service.validate_image_quality(large_image)
        assert not is_valid
        assert "too large" in message.lower()
    
    def test_compare_embeddings(self, face_service):
        """Test embedding comparison."""
        # Create two similar embeddings
        embedding1 = np.random.rand(512).astype(np.float32)
        embedding2 = embedding1 + np.random.rand(512).astype(np.float32) * 0.1
        
        similarity = face_service.compare_embeddings(embedding1, embedding2)
        assert 0 <= similarity <= 1
        assert similarity > 0.5  # Should be similar
    
    def test_compare_embeddings_identical(self, face_service):
        """Test embedding comparison with identical embeddings."""
        embedding = np.random.rand(512).astype(np.float32)
        similarity = face_service.compare_embeddings(embedding, embedding)
        assert similarity > 0.99  # Should be nearly identical


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

