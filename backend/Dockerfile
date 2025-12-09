# =============================================================================
# Face Recognition Attendance System - Docker + CUDA 12 + cuDNN 9
# RTX 3060 va boshqa zamonaviy GPU lar uchun optimallashtirilgan
# =============================================================================

# NVIDIA CUDA 12.2 + cuDNN 9 base image
FROM nvidia/cuda:12.2.2-cudnn9-runtime-ubuntu22.04

# ================================
# Environment Variables
# ================================
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# CUDA paths
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}

# InsightFace model cache
ENV INSIGHTFACE_HOME=/app/.insightface

# Force CUDA usage
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

WORKDIR /app

# ================================
# System Dependencies
# ================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python 3.10
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    # Build essentials
    build-essential \
    cmake \
    pkg-config \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-dev \
    # FFmpeg / RTSP support
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    # Utilities
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python alias
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Upgrade pip
RUN pip3 install --upgrade pip setuptools wheel

# ================================
# Python Dependencies
# ================================
COPY requirements.docker.txt .
RUN pip3 install --no-cache-dir -r requirements.docker.txt

# ================================
# Verify CUDA installation
# ================================
RUN python3 -c "import onnxruntime as ort; providers = ort.get_available_providers(); print('Available providers:', providers); assert 'CUDAExecutionProvider' in providers, 'CUDA not available!'"

# ================================
# Application Code
# ================================
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create directories
RUN mkdir -p /app/images /app/faiss_index /app/data /app/.insightface

# ================================
# Permissions
# ================================
RUN chmod -R 755 /app

# ================================
# Expose & Health Check
# ================================
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ================================
# Run
# ================================
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
