from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./face_attendance.db",
        description="Database connection URL"
    )
    
    # SQLite Database file path
    SQLITE_DB_PATH: str = "./face_attendance.db"
    
    # FAISS
    FAISS_INDEX_PATH: str = "./faiss_index/student_faces.index"
    FAISS_ID_MAP_PATH: str = "./faiss_index/id_map.pkl"
    
    # Storage
    IMAGES_BASE_PATH: str = "./images"
    
    # Face Recognition
    CONFIDENCE_THRESHOLD: float = 0.6
    EMBEDDING_DIMENSION: int = 512
    INSIGHTFACE_MODEL: str = "buffalo_l"
    
    # GPU Settings
    REQUIRE_GPU: bool = False  # Set to True to require GPU (will fail if GPU not available)
    GPU_DEVICE_ID: int = 0  # GPU device ID (0 for first GPU)
    GPU_BATCH_SIZE: int = 8  # Batch size for GPU processing (larger = better GPU utilization)
    GPU_MEMORY_LIMIT_GB: int = 2  # GPU memory limit in GB (0 = unlimited)

    # Multi-face Recognition Settings (Production)
    MAX_FACES_PER_FRAME: int = 20  # Bir kadrda maksimal yuz soni
    RECOGNITION_INTERVAL_MS: int = 500  # Yuz aniqlash oralig'i (millisekund)
    COOLDOWN_SECONDS: int = 10  # Bir xil talaba uchun cooldown (soniya)
    MIN_FACE_SIZE: int = 80  # Minimal yuz o'lchami (piksel)
    FRAME_SKIP: int = 3  # Har nechta kadrda 1 marta aniqlash
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

