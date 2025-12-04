# GPU Linux Setup - To'liq GPU Qo'llab-quvvatlash

Bu backend endi **Linux da 100% GPU ishlatishga tayyor**! Barcha GPU funksiyalari Linux uchun optimallashtirildi.

## ✅ Amalga oshirilgan o'zgarishlar

### 1. Linux GPU Detection
- ✅ Windows DLL tekshiruvlari Linux uchun `.so` library tekshiruvlariga o'zgartirildi
- ✅ LD_LIBRARY_PATH avtomatik sozlanadi
- ✅ CUDA_HOME va CUDA_PATH environment variable'lar qo'llab-quvvatlanadi
- ✅ nvidia-smi orqali GPU mavjudligi tekshiriladi

### 2. ONNX Runtime GPU Optimizatsiyalari
- ✅ Linux uchun CUDA library detection
- ✅ GPU device ID config orqali sozlanadi
- ✅ GPU memory limit sozlanadi
- ✅ Maximum graph optimization yoqildi
- ✅ CUDA provider options optimallashtirildi

### 3. FAISS GPU Support
- ✅ Linux uchun FAISS GPU to'liq qo'llab-quvvatlanadi
- ✅ GPU device ID config orqali sozlanadi
- ✅ Index avtomatik GPU ga transfer qilinadi

### 4. GPU Monitoring
- ✅ nvidia-smi orqali GPU monitoring (Linux va Windows)
- ✅ GPU utilization, memory va temperature tracking
- ✅ Real-time GPU status loglari

## 📦 O'rnatish (Linux)

### 1. CUDA Toolkit o'rnatish

```bash
# CUDA Toolkit 12.x ni o'rnating
# https://developer.nvidia.com/cuda-downloads

# Ubuntu/Debian uchun:
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-4

# Yoki manual installer:
# https://developer.nvidia.com/cuda-12-4-0-download-archive
```

### 2. Environment Variables sozlash

```bash
# ~/.bashrc yoki ~/.zshrc ga qo'shing:
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Yoki faqat LD_LIBRARY_PATH:
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

### 3. Dependencies o'rnatish

```bash
cd backend

# Virtual environment yaratish (agar yo'q bo'lsa)
python3 -m venv env
source env/bin/activate

# GPU dependencies o'rnatish
pip install -r requirements.txt

# FAISS GPU (Linux da pip orqali o'rnatiladi)
pip install faiss-gpu==1.7.4

# ONNX Runtime GPU
pip install onnxruntime-gpu==1.16.3
```

### 4. GPU Tekshiruv

```bash
# GPU va CUDA tekshiruv
python scripts/check_gpu.py

# NVIDIA driverlar tekshiruv
nvidia-smi

# CUDA versiyasi tekshiruv
nvcc --version
```

## ⚙️ Configuration

`app/core/config.py` da GPU sozlamalari:

```python
REQUIRE_GPU: bool = False  # True = GPU majburiy (CPU fallback yo'q)
GPU_DEVICE_ID: int = 0  # GPU device ID (0 = birinchi GPU)
GPU_BATCH_SIZE: int = 8  # Batch size (katta = yaxshi GPU utilization)
GPU_MEMORY_LIMIT_GB: int = 2  # GPU memory limit (0 = cheksiz)
```

Environment variable orqali:

```bash
export REQUIRE_GPU=true  # GPU majburiy
export GPU_DEVICE_ID=0    # GPU device ID
export GPU_BATCH_SIZE=16  # Batch size
export GPU_MEMORY_LIMIT_GB=4  # Memory limit
```

## 🚀 Ishlatish

### Normal ishga tushirish

```bash
cd backend
source env/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Backend avtomatik ravishda:
1. GPU mavjudligini tekshiradi (Linux uchun CUDA libraries)
2. GPU topilsa, GPU da ishlaydi
3. GPU topilmasa, CPU fallback (ogohlantirish bilan)

### GPU Status Loglari

Backend ishga tushganda, loglarida quyidagilar ko'rinadi:

```
✓ CUDA libraries found in system
✓ CUDAExecutionProvider is available
✓ InsightFace initialized successfully with GPU support
✓ FAISS initialized on GPU device 0 for maximum performance!
```

## 🔍 Troubleshooting

### GPU topilmayapti

1. **NVIDIA driverlar o'rnatilganligini tekshiring:**
   ```bash
   nvidia-smi
   ```

2. **CUDA Toolkit o'rnatilganligini tekshiring:**
   ```bash
   nvcc --version
   ls /usr/local/cuda/lib64/libcublas.so*
   ```

3. **LD_LIBRARY_PATH sozlang:**
   ```bash
   export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
   ```

4. **ONNX Runtime GPU tekshiruv:**
   ```bash
   python -c "import onnxruntime as ort; print(ort.get_available_providers())"
   ```
   `CUDAExecutionProvider` ko'rinishi kerak.

### FAISS GPU ishlamayapti

1. **FAISS GPU o'rnatilganligini tekshiring:**
   ```bash
   python -c "import faiss; print(faiss.get_num_gpus())"
   ```
   `1` yoki ko'proq ko'rinishi kerak.

2. **Agar 0 ko'rsatsa:**
   ```bash
   pip uninstall faiss-cpu faiss-gpu
   pip install faiss-gpu==1.7.4
   ```

### CUDA libraries topilmayapti

1. **CUDA_HOME sozlang:**
   ```bash
   export CUDA_HOME=/usr/local/cuda
   export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
   ```

2. **Yoki .env faylida:**
   ```bash
   CUDA_HOME=/usr/local/cuda
   ```

## 📊 Performance

GPU ishlatganda:
- **Face Recognition**: 10-50x tezroq (CPU ga nisbatan)
- **Vector Search**: 5-20x tezroq (CPU ga nisbatan)
- **Batch Processing**: GPU da parallel bajariladi

## ✅ Tekshiruvlar

Barcha GPU funksiyalari to'g'ri ishlayotganini tekshirish:

```bash
# 1. GPU tekshiruv skripti
python scripts/check_gpu.py

# 2. GPU performance test
python scripts/test_gpu_performance.py

# 3. Backend ishga tushirish va loglarni ko'rish
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🎯 Xulosa

Backend endi Linux da **to'liq GPU qo'llab-quvvatlash** bilan ishlaydi:
- ✅ ONNX Runtime GPU (Face Recognition)
- ✅ FAISS GPU (Vector Search)
- ✅ GPU Monitoring
- ✅ Automatic GPU detection
- ✅ CPU fallback (agar GPU topilmasa)

GPU ni majburiy qilish uchun: `export REQUIRE_GPU=true`

