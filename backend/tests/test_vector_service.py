import pytest
import numpy as np
import os
import tempfile
from app.services.vector_service import VectorService


class TestVectorService:
    """Tests for FAISS vector service."""
    
    @pytest.fixture
    def vector_service(self):
        """Create a temporary vector service for testing."""
        # Create temporary directory for test index
        temp_dir = tempfile.mkdtemp()
        index_path = os.path.join(temp_dir, "test_index.index")
        id_map_path = os.path.join(temp_dir, "test_id_map.pkl")
        
        service = VectorService()
        service.index_path = index_path
        service.id_map_path = id_map_path
        
        return service
    
    def test_service_initialization(self, vector_service):
        """Test that vector service initializes correctly."""
        assert vector_service is not None
        assert vector_service.index is not None
        assert vector_service.dimension == 512
    
    def test_add_single_embedding(self, vector_service):
        """Test adding a single embedding."""
        embedding = np.random.rand(512).astype(np.float32)
        student_id = 1
        
        initial_count = vector_service.index.ntotal
        vector_service.add_embedding(embedding, student_id)
        
        assert vector_service.index.ntotal == initial_count + 1
        assert len(vector_service.id_map) == initial_count + 1
    
    def test_add_batch_embeddings(self, vector_service):
        """Test adding multiple embeddings in batch."""
        embeddings = [np.random.rand(512).astype(np.float32) for _ in range(5)]
        student_ids = [1, 2, 3, 4, 5]
        
        initial_count = vector_service.index.ntotal
        vector_service.add_embeddings_batch(embeddings, student_ids)
        
        assert vector_service.index.ntotal == initial_count + 5
        assert len(vector_service.id_map) == initial_count + 5
    
    def test_search_empty_index(self, vector_service):
        """Test search on empty index."""
        embedding = np.random.rand(512).astype(np.float32)
        results = vector_service.search(embedding, k=1)
        assert results == []
    
    def test_search_with_results(self, vector_service):
        """Test search with existing embeddings."""
        # Add some embeddings
        embeddings = [np.random.rand(512).astype(np.float32) for _ in range(5)]
        student_ids = [1, 2, 3, 4, 5]
        vector_service.add_embeddings_batch(embeddings, student_ids)
        
        # Search with first embedding
        results = vector_service.search(embeddings[0], k=1)
        
        assert len(results) > 0
        assert results[0][0] == 1  # Should return student_id 1
        assert results[0][1] > 0.9  # High similarity
    
    def test_search_with_threshold(self, vector_service):
        """Test search with confidence threshold."""
        # Add embeddings
        embedding = np.random.rand(512).astype(np.float32)
        vector_service.add_embedding(embedding, 1)
        
        # Search with same embedding
        result = vector_service.search_with_threshold(embedding, threshold=0.9)
        
        assert result is not None
        assert result[0] == 1
        assert result[1] > 0.9
    
    def test_search_below_threshold(self, vector_service):
        """Test search with result below threshold."""
        # Add one embedding
        embedding1 = np.random.rand(512).astype(np.float32)
        vector_service.add_embedding(embedding1, 1)
        
        # Search with completely different embedding
        embedding2 = np.random.rand(512).astype(np.float32)
        result = vector_service.search_with_threshold(embedding2, threshold=0.99)
        
        # Might not match due to high threshold
        assert result is None or result[1] < 0.99
    
    def test_get_stats(self, vector_service):
        """Test getting index statistics."""
        # Add some embeddings
        embeddings = [np.random.rand(512).astype(np.float32) for _ in range(3)]
        student_ids = [1, 2, 3]
        vector_service.add_embeddings_batch(embeddings, student_ids)
        
        stats = vector_service.get_stats()
        
        assert stats["total_vectors"] == 3
        assert stats["dimension"] == 512
        assert stats["total_students"] == 3
    
    def test_save_and_load_index(self, vector_service):
        """Test saving and loading index."""
        # Add embeddings
        embeddings = [np.random.rand(512).astype(np.float32) for _ in range(3)]
        student_ids = [1, 2, 3]
        vector_service.add_embeddings_batch(embeddings, student_ids)
        
        # Save
        vector_service.save_index()
        
        # Create new service with same paths
        new_service = VectorService()
        new_service.index_path = vector_service.index_path
        new_service.id_map_path = vector_service.id_map_path
        new_service._load_index()
        
        # Verify
        assert new_service.index.ntotal == 3
        assert len(new_service.id_map) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

