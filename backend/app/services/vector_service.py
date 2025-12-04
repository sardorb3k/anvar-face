import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional, Dict
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """FAISS vector service for similarity search of face embeddings with GPU acceleration."""
    
    def __init__(self):
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index_path = settings.FAISS_INDEX_PATH
        self.id_map_path = settings.FAISS_ID_MAP_PATH
        self.index = None
        self.gpu_index = None  # GPU version of index
        self.res = None  # GPU resource
        self.id_map = []  # Maps FAISS index position to student database ID
        self.use_ivf = False
        self.trained = False
        self.use_gpu = False
        self.gpu_available = False
        
        # Check GPU availability
        self._check_gpu_availability()
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Load or create index
        self._initialize_index()
    
    def _check_gpu_availability(self):
        """Check if GPU is available for FAISS."""
        try:
            ngpus = faiss.get_num_gpus()
            if ngpus > 0:
                self.gpu_available = True
                logger.info(f"✓ GPU available for FAISS: {ngpus} GPU(s) detected")
            else:
                logger.info("ℹ FAISS GPU not available, using CPU (GPU support requires CUDA)")
                self.gpu_available = False
        except Exception as e:
            logger.info(f"ℹ FAISS GPU check: {e}. Using CPU fallback (this is normal if CUDA is not installed).")
            self.gpu_available = False
    
    def _initialize_index(self):
        """Initialize or load FAISS index."""
        if os.path.exists(self.index_path) and os.path.exists(self.id_map_path):
            self._load_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index (GPU if available, otherwise CPU)."""
        logger.info("Creating new FAISS IndexFlatIP")
        
        # Create CPU index first (required as base)
        cpu_index = faiss.IndexFlatIP(self.dimension)
        
        # Try to use GPU if available
        if self.gpu_available:
            try:
                logger.info("Initializing FAISS on GPU...")
                self.res = faiss.StandardGpuResources()
                gpu_device_id = settings.GPU_DEVICE_ID
                self.gpu_index = faiss.index_cpu_to_gpu(self.res, gpu_device_id, cpu_index)
                self.index = cpu_index  # Keep CPU index as backup
                self.use_gpu = True
                logger.info(f"✓ FAISS initialized on GPU device {gpu_device_id} for maximum performance!")
            except Exception as e:
                logger.warning(f"⚠ Failed to initialize FAISS GPU: {e}. Using CPU.")
                self.index = cpu_index
                self.use_gpu = False
        else:
            self.index = cpu_index
            self.use_gpu = False
            logger.info("Using CPU index (GPU not available)")
        
        self.id_map = []
        logger.info(f"Created new index with dimension {self.dimension}")
    
    def _load_index(self):
        """Load FAISS index from disk and transfer to GPU if available."""
        try:
            logger.info(f"Loading FAISS index from {self.index_path}")
            cpu_index = faiss.read_index(self.index_path)
            
            with open(self.id_map_path, 'rb') as f:
                self.id_map = pickle.load(f)
            
            logger.info(f"Loaded index with {cpu_index.ntotal} vectors")
            
            # Transfer to GPU if available
            if self.gpu_available and cpu_index.ntotal > 0:
                try:
                    logger.info("Transferring FAISS index to GPU...")
                    if self.res is None:
                        self.res = faiss.StandardGpuResources()
                    gpu_device_id = settings.GPU_DEVICE_ID
                    self.gpu_index = faiss.index_cpu_to_gpu(self.res, gpu_device_id, cpu_index)
                    self.index = cpu_index  # Keep CPU index as backup
                    self.use_gpu = True
                    logger.info(f"✓ FAISS index transferred to GPU device {gpu_device_id}!")
                except Exception as e:
                    logger.warning(f"⚠ Failed to transfer index to GPU: {e}. Using CPU.")
                    self.index = cpu_index
                    self.use_gpu = False
            else:
                self.index = cpu_index
                self.use_gpu = False
                
        except Exception as e:
            logger.error(f"Failed to load index: {e}. Creating new index.")
            self._create_new_index()
    
    def save_index(self):
        """Save FAISS index to disk."""
        try:
            logger.info(f"Saving FAISS index to {self.index_path}")
            # Save CPU index (GPU index is synced)
            index_to_save = self.index
            
            # If using GPU, we need to sync GPU -> CPU before saving
            if self.use_gpu and self.gpu_index is not None:
                # GPU index has the latest data, so we update CPU index from GPU
                # For now, we keep both in sync by always updating both
                pass
            
            faiss.write_index(index_to_save, self.index_path)
            
            with open(self.id_map_path, 'wb') as f:
                pickle.dump(self.id_map, f)
            
            logger.info(f"Saved index with {index_to_save.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise
    
    def add_embedding(self, embedding: np.ndarray, student_db_id: int):
        """
        Add a single embedding to the index (GPU accelerated if available).
        
        Args:
            embedding: Face embedding vector (512-dimensional)
            student_db_id: Student's database ID
        """
        # Ensure embedding is normalized and in correct shape
        embedding = embedding.astype(np.float32)
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embedding)
        
        # Add to index (GPU if available)
        if self.use_gpu and self.gpu_index is not None:
            self.gpu_index.add(embedding)
            # Also add to CPU index to keep in sync
            self.index.add(embedding)
        else:
            self.index.add(embedding)
        
        self.id_map.append(student_db_id)
        
        total = self.index.ntotal
        logger.info(f"Added embedding for student {student_db_id}. Total vectors: {total} [GPU: {'✓' if self.use_gpu else '✗'}]")
        
        # Auto-save every 100 additions
        if total % 100 == 0:
            self.save_index()
    
    def add_embeddings_batch(self, embeddings: List[np.ndarray], student_db_ids: List[int]):
        """
        Add multiple embeddings in batch (GPU accelerated if available).
        
        Args:
            embeddings: List of face embedding vectors
            student_db_ids: List of student database IDs
        """
        if len(embeddings) != len(student_db_ids):
            raise ValueError("Number of embeddings must match number of student IDs")
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Add to index (GPU if available - much faster for batches!)
        if self.use_gpu and self.gpu_index is not None:
            self.gpu_index.add(embeddings_array)
            # Also add to CPU index to keep in sync
            self.index.add(embeddings_array)
        else:
            self.index.add(embeddings_array)
        
        self.id_map.extend(student_db_ids)
        
        total = self.index.ntotal
        logger.info(f"Added {len(embeddings)} embeddings. Total vectors: {total} [GPU: {'✓' if self.use_gpu else '✗'}]")
        
        # Save index
        self.save_index()
    
    def search(self, embedding: np.ndarray, k: int = 1) -> List[Tuple[int, float]]:
        """
        Search for similar embeddings (GPU accelerated if available).
        
        Args:
            embedding: Query embedding vector
            k: Number of nearest neighbors to return
            
        Returns:
            List of tuples (student_db_id, similarity_score)
        """
        total_vectors = self.gpu_index.ntotal if (self.use_gpu and self.gpu_index is not None) else self.index.ntotal
        if total_vectors == 0:
            logger.warning("Index is empty")
            return []
        
        # Ensure embedding is normalized and in correct shape
        embedding = embedding.astype(np.float32)
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embedding)
        
        # Search (use GPU if available for faster search)
        k = min(k, total_vectors)  # Don't request more than available
        
        if self.use_gpu and self.gpu_index is not None:
            distances, indices = self.gpu_index.search(embedding, k)
        else:
            distances, indices = self.index.search(embedding, k)
        
        # Convert to list of (student_id, similarity)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.id_map):  # Valid index
                student_id = self.id_map[idx]
                similarity = float(dist)  # Already cosine similarity due to normalized vectors
                results.append((student_id, similarity))
        
        return results
    
    def search_with_threshold(self, embedding: np.ndarray, threshold: float = None) -> Optional[Tuple[int, float]]:
        """
        Search for matching face with confidence threshold.
        
        Args:
            embedding: Query embedding vector
            threshold: Minimum similarity threshold (default from settings)
            
        Returns:
            Tuple of (student_db_id, similarity_score) or None if no match above threshold
        """
        if threshold is None:
            threshold = settings.CONFIDENCE_THRESHOLD
        
        results = self.search(embedding, k=1)
        
        if not results:
            return None
        
        student_id, similarity = results[0]
        
        if similarity >= threshold:
            logger.info(f"Match found: student_id={student_id}, similarity={similarity:.4f}")
            return (student_id, similarity)
        else:
            logger.info(f"No match above threshold. Best: similarity={similarity:.4f} < {threshold}")
            return None
    
    def remove_student_embeddings(self, student_db_id: int):
        """
        Remove all embeddings for a student.
        Note: FAISS doesn't support efficient deletion, so we rebuild the index.
        
        Args:
            student_db_id: Student's database ID
        """
        logger.info(f"Removing embeddings for student {student_db_id}")
        
        # Find indices to keep
        keep_indices = [i for i, sid in enumerate(self.id_map) if sid != student_db_id]
        
        if len(keep_indices) == len(self.id_map):
            logger.warning(f"No embeddings found for student {student_db_id}")
            return
        
        # Get all vectors
        all_vectors = []
        for i in keep_indices:
            vector = self.index.reconstruct(int(i))
            all_vectors.append(vector)
        
        # Rebuild index
        self._create_new_index()
        
        if all_vectors:
            vectors_array = np.array(all_vectors, dtype=np.float32)
            # Use batch add which will use GPU if available
            self.add_embeddings_batch(
                [v for v in vectors_array],
                [self.id_map[i] for i in keep_indices]
            )
        
        total = self.gpu_index.ntotal if (self.use_gpu and self.gpu_index is not None) else self.index.ntotal
        logger.info(f"Removed embeddings. Remaining vectors: {total}")
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        total = self.gpu_index.ntotal if (self.use_gpu and self.gpu_index is not None) else self.index.ntotal
        return {
            "total_vectors": total,
            "dimension": self.dimension,
            "index_type": "IndexFlatIP",
            "total_students": len(set(self.id_map)) if self.id_map else 0,
            "gpu_enabled": self.use_gpu,
            "gpu_available": self.gpu_available
        }
    
    def upgrade_to_ivf(self, nlist: int = 100):
        """
        Upgrade to IVF index for better performance with large datasets.
        Recommended when number of students > 1000.
        Supports GPU acceleration if available.
        
        Args:
            nlist: Number of clusters
        """
        total = self.gpu_index.ntotal if (self.use_gpu and self.gpu_index is not None) else self.index.ntotal
        if total < 1000:
            logger.warning("IVF upgrade recommended only for >1000 vectors")
            return
        
        logger.info(f"Upgrading to IndexIVFFlat with {nlist} clusters [GPU: {'✓' if self.use_gpu else '✗'}]")
        
        # Get all vectors from current index
        all_vectors = []
        index_to_read = self.gpu_index if (self.use_gpu and self.gpu_index is not None) else self.index
        for i in range(total):
            vector = index_to_read.reconstruct(int(i))
            all_vectors.append(vector)
        
        vectors_array = np.array(all_vectors, dtype=np.float32)
        
        # Create IVF index
        quantizer = faiss.IndexFlatIP(self.dimension)
        ivf_index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist, faiss.METRIC_INNER_PRODUCT)
        
        # Train index
        ivf_index.train(vectors_array)
        
        # Add vectors
        ivf_index.add(vectors_array)
        
        # Set search parameters
        ivf_index.nprobe = 10  # Search 10 clusters
        
        # Transfer to GPU if available
        if self.gpu_available:
            try:
                if self.res is None:
                    self.res = faiss.StandardGpuResources()
                gpu_device_id = settings.GPU_DEVICE_ID
                gpu_ivf_index = faiss.index_cpu_to_gpu(self.res, gpu_device_id, ivf_index)
                self.gpu_index = gpu_ivf_index
                self.use_gpu = True
                logger.info(f"✓ IVF index transferred to GPU device {gpu_device_id}")
            except Exception as e:
                logger.warning(f"⚠ Failed to transfer IVF index to GPU: {e}. Using CPU.")
                self.use_gpu = False
        
        # Replace old index
        self.index = ivf_index
        self.use_ivf = True
        self.trained = True
        
        self.save_index()
        logger.info(f"Upgraded to IVF index with {total} vectors")


# Global instance
_vector_service = None


def get_vector_service() -> VectorService:
    """Get or create global vector service instance."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service

