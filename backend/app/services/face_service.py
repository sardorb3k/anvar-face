import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from typing import List, Optional, Tuple, Dict
import logging
import onnxruntime
import os
import sys
from pathlib import Path
from app.core.config import settings
from app.services.gpu_monitor import get_gpu_monitor

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Face recognition service using InsightFace for detection and embedding extraction."""
    
    def __init__(self):
        self.app = None
        self.model_name = settings.INSIGHTFACE_MODEL
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
        self._initialize_model()
    
    def _find_cuda_libraries(self) -> bool:
        """Find and configure CUDA libraries for Windows or Linux."""
        if sys.platform == 'win32':
            # Windows: Find and add CUDA DLL paths to PATH
            cuda_paths = [
                os.environ.get('CUDA_PATH'),
                os.environ.get('CUDA_PATH_V13_0'),
                os.environ.get('CUDA_PATH_V12_4'),
                os.environ.get('CUDA_PATH_V12_3'),
                os.environ.get('CUDA_PATH_V12_2'),
                os.environ.get('CUDA_PATH_V12_1'),
                os.environ.get('CUDA_PATH_V12_0'),
                r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0',
                r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4',
                r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.3',
                r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2',
                r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1',
                r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0',
                r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8',
            ]
            
            cuda_bin_paths = []
            for cuda_path in cuda_paths:
                if cuda_path and os.path.exists(cuda_path):
                    bin_path = os.path.join(cuda_path, 'bin')
                    if os.path.exists(bin_path):
                        cuda_bin_paths.append(bin_path)
            
            # Check for CUDA DLL files (both 12.x and 13.x)
            # Try multiple DLL variants for better compatibility
            dll_found = False
            dll_version = None
            found_bin_path = None
            
            for bin_path in cuda_bin_paths:
                # Try multiple DLL name variants
                dll_variants = [
                    ('cublasLt64_13.dll', '13.0'),
                    ('cublasLt64_12.dll', '12.x'),
                    ('cublas64_13.dll', '13.0 (alt)'),
                    ('cublas64_12.dll', '12.x (alt)'),
                    ('cublasLt64.dll', 'generic'),
                    ('cublas64.dll', 'generic (alt)'),
                ]
                
                # Also check for any cublas DLL using glob
                import glob
                cublas_dlls = glob.glob(os.path.join(bin_path, '*cublas*.dll'))
                if cublas_dlls:
                    dll_found = True
                    dll_version = "detected"
                    found_bin_path = bin_path
                    logger.info(f"Found CUDA DLL: {os.path.basename(cublas_dlls[0])} in {bin_path}")
                    break
                
                # Try specific variants
                for dll_name, version in dll_variants:
                    dll_path = os.path.join(bin_path, dll_name)
                    if os.path.exists(dll_path):
                        dll_found = True
                        dll_version = version
                        found_bin_path = bin_path
                        logger.info(f"Found CUDA DLL: {dll_name} ({version}) in {bin_path}")
                        break
                
                if dll_found:
                    break
            
            # Add to PATH if found
            if dll_found and found_bin_path:
                path_env = os.environ.get('PATH', '')
                if found_bin_path not in path_env.split(os.pathsep):
                    os.environ['PATH'] = found_bin_path + os.pathsep + path_env
                    logger.info(f"✓ Added CUDA bin path to PATH: {found_bin_path}")
            
            if not dll_found:
                logger.warning("CUDA DLL (cublasLt64_12.dll or cublasLt64_13.dll) not found in common CUDA paths")
                logger.warning("Please install CUDA Toolkit 12.x/13.x or add CUDA bin directory to PATH")
                return False
            else:
                logger.info(f"✓ CUDA {dll_version} DLL found and added to PATH")
            
            return True
        else:
            # Linux/Unix: Check for CUDA libraries in standard locations
            # On Linux, CUDA libraries are typically in:
            # - /usr/local/cuda/lib64
            # - /usr/lib/x86_64-linux-gnu
            # - LD_LIBRARY_PATH environment variable
            
            cuda_lib_paths = [
                os.environ.get('CUDA_HOME'),
                os.environ.get('CUDA_PATH'),
                '/usr/local/cuda',
                '/usr/local/cuda-12.4',
                '/usr/local/cuda-12.3',
                '/usr/local/cuda-12.2',
                '/usr/local/cuda-12.1',
                '/usr/local/cuda-12.0',
                '/usr/local/cuda-11.8',
            ]
            
            # Check for libcublas.so (CUDA library)
            lib_found = False
            for cuda_path in cuda_lib_paths:
                if cuda_path and os.path.exists(cuda_path):
                    lib_path = os.path.join(cuda_path, 'lib64')
                    if os.path.exists(lib_path):
                        # Check for CUDA libraries
                        import glob
                        cublas_libs = glob.glob(os.path.join(lib_path, 'libcublas*.so*'))
                        if cublas_libs:
                            lib_found = True
                            # Add to LD_LIBRARY_PATH if not already there
                            ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
                            if lib_path not in ld_library_path.split(':'):
                                os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{ld_library_path}" if ld_library_path else lib_path
                                logger.info(f"Added CUDA lib64 path to LD_LIBRARY_PATH: {lib_path}")
                            break
            
            # Also check if CUDA libraries are in system paths
            if not lib_found:
                import ctypes.util
                # Try to find libcublas using ctypes
                cublas_path = ctypes.util.find_library('cublas')
                if cublas_path:
                    lib_found = True
                    logger.info(f"✓ CUDA library found in system: {cublas_path}")
            
            # On Linux, if nvidia-smi works, CUDA is likely available
            # ONNX Runtime will handle library loading automatically
            if not lib_found:
                # Check if nvidia-smi is available (indicates NVIDIA drivers)
                try:
                    import subprocess
                    result = subprocess.run(['nvidia-smi', '--version'], 
                                          capture_output=True, timeout=2)
                    if result.returncode == 0:
                        logger.info("✓ NVIDIA drivers detected (nvidia-smi available)")
                        logger.info("CUDA libraries will be loaded automatically by ONNX Runtime")
                        return True
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    pass
                
                logger.warning("CUDA libraries not found in standard locations")
                logger.warning("ONNX Runtime will attempt to load CUDA libraries automatically")
                logger.warning("If GPU doesn't work, ensure CUDA Toolkit is installed and LD_LIBRARY_PATH is set")
                # Don't fail on Linux - let ONNX Runtime try to load libraries
                return True
            
            return True
    
    def _check_gpu_availability(self) -> bool:
        """Check if CUDA GPU is available for onnxruntime."""
        try:
            # First try to find CUDA libraries (Windows DLLs or Linux .so files)
            if not self._find_cuda_libraries():
                if sys.platform == 'win32':
                    logger.error("CUDA DLLs not found. Please install CUDA Toolkit.")
                    return False
                # On Linux, continue anyway - ONNX Runtime may still work
            
            available_providers = onnxruntime.get_available_providers()
            logger.info(f"Available ONNX Runtime providers: {available_providers}")
            
            if 'CUDAExecutionProvider' in available_providers:
                logger.info("✓ CUDAExecutionProvider is available in providers list")
                
                # Try to create a test session to verify GPU actually works
                try:
                    import tempfile
                    import numpy as np
                    # Create a minimal test
                    test_providers = ['CUDAExecutionProvider']
                    # Just check if provider can be used (we'll get error if DLLs missing)
                    logger.info("Testing CUDAExecutionProvider...")
                    return True
                except Exception as e:
                    logger.warning(f"CUDAExecutionProvider listed but may not work: {e}")
                    return False
            else:
                logger.warning("CUDAExecutionProvider is NOT in available providers")
                logger.warning("Make sure onnxruntime-gpu is installed and CUDA is properly configured")
                return False
        except Exception as e:
            logger.error(f"Error checking GPU availability: {e}")
            return False
    
    def _initialize_model(self):
        """Initialize InsightFace model with GPU support and optimizations (onnxruntime-gpu required)."""
        # Check if GPU is required (via environment variable)
        require_gpu = os.environ.get('REQUIRE_GPU', 'false').lower() == 'true'
        
        # First check if GPU is available
        gpu_available = self._check_gpu_availability()

        if not gpu_available:
            if sys.platform == 'win32':
                error_msg = (
                    "\n" + "="*70 + "\n"
                    "⚠ GPU is not available!\n\n"
                    "MUAMMO: cublasLt64_12.dll topilmayapti (CUDA Toolkit o'rnatilmagan)\n\n"
                    "YECHIM:\n"
                    "1. CUDA Toolkit 12.x ni o'rnating:\n"
                    "   https://developer.nvidia.com/cuda-downloads\n\n"
                    "2. O'rnatgandan keyin, CUDA bin papkasini PATH ga qo'shing:\n"
                    "   Masalan: C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.4\\bin\n\n"
                    "3. Yoki environment variable qo'shing:\n"
                    "   CUDA_PATH=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.4\n\n"
                    "4. Ilovani qayta ishga tushiring\n\n"
                    "NOTA BENE: Agar GPU o'rnatish qiyin bo'lsa, CPU fallback ishlatiladi.\n"
                    "Lekin CPU 100% bo'lib ketadi va sekin ishlaydi.\n"
                    "GPU ni majburiy qilish uchun: set REQUIRE_GPU=true\n"
                    "="*70
                )
            else:
                error_msg = (
                    "\n" + "="*70 + "\n"
                    "⚠ GPU is not available!\n\n"
                    "MUAMMO: CUDA libraries topilmayapti yoki CUDAExecutionProvider mavjud emas\n\n"
                    "YECHIM (Linux):\n"
                    "1. CUDA Toolkit 12.x ni o'rnating:\n"
                    "   https://developer.nvidia.com/cuda-downloads\n\n"
                    "2. O'rnatgandan keyin, LD_LIBRARY_PATH ga qo'shing:\n"
                    "   export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH\n\n"
                    "3. Yoki environment variable qo'shing:\n"
                    "   export CUDA_HOME=/usr/local/cuda\n\n"
                    "4. NVIDIA driverlar o'rnatilganligini tekshiring:\n"
                    "   nvidia-smi\n\n"
                    "5. Ilovani qayta ishga tushiring\n\n"
                    "NOTA BENE: Agar GPU o'rnatish qiyin bo'lsa, CPU fallback ishlatiladi.\n"
                    "Lekin CPU 100% bo'lib ketadi va sekin ishlaydi.\n"
                    "GPU ni majburiy qilish uchun: export REQUIRE_GPU=true\n"
                    "="*70
                )
            logger.error(error_msg)
            
            if require_gpu:
                raise RuntimeError("GPU initialization failed: CUDA Toolkit not found. REQUIRE_GPU=true is set.")
            
            # Continue with CPU fallback
            logger.warning("⚠ GPU topilmadi, CPU fallback ishlatiladi (sekin ishlaydi)")
        
        try:
            if gpu_available:
                # Initialize with GPU first, CPU as fallback
                logger.info("Initializing InsightFace with GPU support and optimizations...")
                
                # Set ONNX Runtime environment variables for maximum GPU performance
                # These are read by ONNX Runtime internally
                os.environ.setdefault('ORT_GRAPH_OPT_LEVEL', '99')  # Maximum graph optimization
                os.environ.setdefault('ORT_ENABLE_BASIC', '1')
                os.environ.setdefault('ORT_ENABLE_EXTENDED', '1')
                os.environ.setdefault('ORT_ENABLE_LAYOUT_OPT', '1')
                os.environ.setdefault('ORT_ENABLE_MEMORY_PATTERN', '1')
                
                # Configure CUDA provider options for better GPU performance
                gpu_device_id = settings.GPU_DEVICE_ID
                gpu_memory_limit = settings.GPU_MEMORY_LIMIT_GB
                
                # CUDA provider options
                cuda_provider_options = {
                    'device_id': gpu_device_id,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'gpu_mem_limit': gpu_memory_limit * 1024 * 1024 * 1024 if gpu_memory_limit > 0 else 0,
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }
                
                # Try GPU first, but allow CPU fallback if GPU fails
                # InsightFace will automatically use GPU if CUDAExecutionProvider is available
                self.app = FaceAnalysis(
                    name=self.model_name,
                    providers=[
                        ('CUDAExecutionProvider', cuda_provider_options),
                        'CPUExecutionProvider'
                    ]  # GPU first with options, CPU fallback
                )
                # ctx_id=0 means use GPU device 0 (or use settings.GPU_DEVICE_ID)
                self.app.prepare(ctx_id=gpu_device_id, det_size=(640, 640))
                logger.info(f"✓ GPU optimizations enabled: maximum graph optimization, GPU device {gpu_device_id}")
                if gpu_memory_limit > 0:
                    logger.info(f"✓ GPU memory limit: {gpu_memory_limit}GB")
            else:
                # Initialize with CPU only
                logger.info("Initializing InsightFace with CPU (GPU not available)...")
                self.app = FaceAnalysis(
                    name=self.model_name,
                    providers=['CPUExecutionProvider']  # CPU only
                )
                self.app.prepare(ctx_id=-1, det_size=(640, 640))  # ctx_id=-1 for CPU
            
            # Verify that GPU is actually being used
            gpu_active = False
            cpu_active = False
            
            if hasattr(self.app, 'det_model') and hasattr(self.app.det_model, 'session'):
                session = self.app.det_model.session
                if hasattr(session, '_providers'):
                    active_providers = session._providers
                    logger.info(f"Detection model providers: {active_providers}")
                    if 'CUDAExecutionProvider' in active_providers:
                        gpu_active = True
                        logger.info("✓ GPU (CUDAExecutionProvider) is ACTIVE for detection!")
                    elif 'CPUExecutionProvider' in active_providers:
                        cpu_active = True
                        logger.warning("⚠ Using CPUExecutionProvider for detection (sekin)")
            
            # Check all models
            for model_name, model in self.app.models.items():
                if hasattr(model, 'session'):
                    session = model.session
                    if hasattr(session, '_providers'):
                        providers = session._providers
                        logger.info(f"Model '{model_name}' providers: {providers}")
                        if 'CUDAExecutionProvider' in providers:
                            gpu_active = True
                        elif 'CPUExecutionProvider' in providers:
                            cpu_active = True
            
            if gpu_active:
                logger.info("✓ InsightFace initialized successfully with GPU support")
                # Log GPU status
                try:
                    gpu_monitor = get_gpu_monitor()
                    gpu_monitor.log_gpu_status()
                except Exception as e:
                    logger.debug(f"Could not log GPU status: {e}")
            elif cpu_active:
                logger.warning("⚠ InsightFace initialized with CPU (GPU not available)")
                logger.warning("⚠ CPU 100% bo'lib ketishi mumkin - GPU ni o'rnating!")
            else:
                logger.error("✗ Hech qanday provider faollashtirilmadi!")
                raise RuntimeError("No execution provider active!")
        except RuntimeError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            if sys.platform == 'win32':
                error_msg = (
                    f"\nFailed to initialize InsightFace with GPU: {e}\n\n"
                    "MUAMMO: CUDA DLLs topilmayapti (cublasLt64_12.dll)\n\n"
                    "YECHIM:\n"
                    "1. CUDA Toolkit 12.x ni o'rnating:\n"
                    "   https://developer.nvidia.com/cuda-downloads\n\n"
                    "2. O'rnatgandan keyin PATH ga qo'shing:\n"
                    "   C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.x\\bin\n\n"
                    "3. Ilovani qayta ishga tushiring\n"
                )
            else:
                error_msg = (
                    f"\nFailed to initialize InsightFace with GPU: {e}\n\n"
                    "MUAMMO: CUDA libraries topilmayapti yoki CUDAExecutionProvider ishlamayapti\n\n"
                    "YECHIM (Linux):\n"
                    "1. CUDA Toolkit 12.x ni o'rnating:\n"
                    "   https://developer.nvidia.com/cuda-downloads\n\n"
                    "2. O'rnatgandan keyin LD_LIBRARY_PATH ga qo'shing:\n"
                    "   export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH\n\n"
                    "3. NVIDIA driverlar o'rnatilganligini tekshiring:\n"
                    "   nvidia-smi\n\n"
                    "4. Ilovani qayta ishga tushiring\n"
                )
            logger.error(error_msg)
            raise RuntimeError(f"GPU initialization failed: {e}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for face detection."""
        # Convert to BGR if needed (InsightFace expects BGR)
        if len(image.shape) == 2:  # Grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:  # RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        
        return image
    
    def detect_faces(self, image: np.ndarray) -> List:
        """
        Detect faces in an image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of detected faces with bounding boxes and landmarks
        """
        try:
            image = self.preprocess_image(image)
            faces = self.app.get(image)
            return faces
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []
    
    def extract_embedding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract face embedding from an image (single face - for student registration).

        Args:
            image: Input image as numpy array

        Returns:
            512-dimensional embedding vector or None if no face detected
        """
        try:
            faces = self.detect_faces(image)

            if not faces:
                logger.warning("No face detected in image")
                return None

            if len(faces) > 1:
                logger.warning(f"Multiple faces detected ({len(faces)}). Using the largest face.")
                # Sort by bounding box area and take the largest
                faces = sorted(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)

            # Get embedding from the first (or largest) face
            embedding = faces[0].embedding

            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)

            return embedding

        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return None

    def extract_all_embeddings(self, image: np.ndarray) -> List[Tuple[np.ndarray, dict]]:
        """
        Extract embeddings from ALL faces in an image (for multi-face attendance).

        Args:
            image: Input image as numpy array

        Returns:
            List of tuples (embedding, face_info) for each detected face
            face_info contains: bbox, det_score, face_size
        """
        try:
            faces = self.detect_faces(image)

            if not faces:
                return []

            results = []
            min_face_size = settings.MIN_FACE_SIZE
            max_faces = settings.MAX_FACES_PER_FRAME

            # Filter and sort faces by size (largest first)
            valid_faces = []
            for face in faces:
                face_width = face.bbox[2] - face.bbox[0]
                face_height = face.bbox[3] - face.bbox[1]
                face_size = min(face_width, face_height)

                # Skip too small faces
                if face_size < min_face_size:
                    continue

                # Skip low confidence detections
                if hasattr(face, 'det_score') and face.det_score < 0.5:
                    continue

                valid_faces.append((face, face_size))

            # Sort by size and limit
            valid_faces.sort(key=lambda x: x[1], reverse=True)
            valid_faces = valid_faces[:max_faces]

            for face, face_size in valid_faces:
                embedding = face.embedding
                # Normalize embedding
                embedding = embedding / np.linalg.norm(embedding)

                face_info = {
                    'bbox': face.bbox.tolist(),
                    'det_score': float(face.det_score) if hasattr(face, 'det_score') else 1.0,
                    'face_size': face_size
                }

                results.append((embedding, face_info))

            logger.info(f"Extracted {len(results)} face embeddings from frame")
            return results

        except Exception as e:
            logger.error(f"Multi-face embedding extraction failed: {e}")
            return []
    
    def extract_embeddings_batch(self, images: List[np.ndarray], batch_size: int = None) -> List[Optional[np.ndarray]]:
        """
        Extract embeddings from multiple images in batch (optimized for GPU).
        
        GPU performs better with batch processing, so we process multiple images
        together for better GPU utilization.
        
        Args:
            images: List of input images
            batch_size: Number of images to process in parallel (default from settings.GPU_BATCH_SIZE)
            
        Returns:
            List of embeddings (None for images without faces)
        """
        if batch_size is None:
            batch_size = settings.GPU_BATCH_SIZE
        
        embeddings = []
        total = len(images)
        
        # Process in batches for better GPU utilization
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_images = images[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}/{(total + batch_size - 1)//batch_size} "
                       f"(images {batch_start+1}-{batch_end}/{total})")
            
            # Process each image in the batch
            for i, image in enumerate(batch_images):
                embedding = self.extract_embedding(image)
                embeddings.append(embedding)
        
        return embeddings
    
    def validate_image_quality(self, image: np.ndarray) -> Tuple[bool, str]:
        """
        Validate image quality for face recognition.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check image dimensions
        if image.shape[0] < 100 or image.shape[1] < 100:
            return False, "Image too small (minimum 100x100 pixels)"
        
        # Check if image is too large
        if image.shape[0] > 4000 or image.shape[1] > 4000:
            return False, "Image too large (maximum 4000x4000 pixels)"
        
        # Detect faces
        faces = self.detect_faces(image)
        
        if not faces:
            return False, "No face detected in image"
        
        if len(faces) > 1:
            return False, f"Multiple faces detected ({len(faces)}). Please ensure only one face per image"
        
        # Check face size (should be at least 80x80 pixels)
        face = faces[0]
        face_width = face.bbox[2] - face.bbox[0]
        face_height = face.bbox[3] - face.bbox[1]
        
        if face_width < 80 or face_height < 80:
            return False, "Face too small (minimum 80x80 pixels)"
        
        # Check detection confidence
        if hasattr(face, 'det_score') and face.det_score < 0.5:
            return False, f"Low face detection confidence ({face.det_score:.2f})"
        
        return True, "Image quality is good"
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compare two face embeddings using cosine similarity.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0 to 1, higher is more similar)
        """
        # Normalize embeddings
        embedding1 = embedding1 / np.linalg.norm(embedding1)
        embedding2 = embedding2 / np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2)
        
        return float(similarity)


# Global instance
_face_service = None


def get_face_service() -> FaceRecognitionService:
    """Get or create global face recognition service instance."""
    global _face_service
    if _face_service is None:
        _face_service = FaceRecognitionService()
    return _face_service

