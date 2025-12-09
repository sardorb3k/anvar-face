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

    # Multi-face Recognition Settings (Optimized for speed)
    MAX_FACES_PER_FRAME: int = 10  # Bir kadrda maksimal yuz soni
    RECOGNITION_INTERVAL_MS: int = 300  # Yuz aniqlash oralig'i (1000 dan 300 ga - 0.3 sekund)
    COOLDOWN_SECONDS: int = 10  # Bir xil talaba uchun cooldown (15 dan 10 ga)
    MIN_FACE_SIZE: int = 60  # Minimal yuz o'lchami (80 dan 60 ga - kichikroq yuzlarni ham aniqlash)
    FRAME_SKIP: int = 2  # Har nechta kadrda 1 marta aniqlash (5 dan 2 ga - tezroq)

    # Room Presence Settings
    PRESENCE_TIMEOUT_SECONDS: int = 30  # Xonadan chiqdi deb hisoblash vaqti (soniya)
    PRESENCE_CLEANUP_INTERVAL: int = 10  # Eskirgan presence ni tozalash oralig'i (soniya)
    MAX_SIMULTANEOUS_STREAMS: int = 20  # Maksimal parallel RTSP stream soni
    MAX_CAMERAS_PER_ROOM: int = 10  # Bir xonada maksimal kamera soni
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

