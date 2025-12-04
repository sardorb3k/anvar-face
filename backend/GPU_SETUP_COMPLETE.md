# GPU Setup - To'liq Qo'llab-quvvatlash (Windows va Linux)

Backend endi **Windows va Linux da 100% GPU ishlatishga tayyor**! Barcha GPU funksiyalari ikkala platforma uchun optimallashtirildi.

## ✅ Amalga oshirilgan o'zgarishlar

### 1. Universal GPU Detection
- ✅ **Windows**: CUDA DLL'lar avtomatik topiladi va PATH ga qo'shiladi
- ✅ **Linux**: CUDA libraries avtomatik topiladi va LD_LIBRARY_PATH ga qo'shiladi
- ✅ Barcha CUDA versiyalari qo'llab-quvvatlanadi (11.8, 12.0-12.4, 13.0)
- ✅ Platforma-agnostic kod (Windows va Linux uchun bir xil)

### 2. ONNX Runtime GPU Optimizatsiyalari
- ✅ Platforma-agnostic GPU detection
- ✅ GPU device ID config orqali sozlanadi
- ✅ GPU memory limit sozlanadi
- ✅ Maximum graph optimization yoqildi
- ✅ CUDA provider options optimallashtirildi

### 3. FAISS GPU Support
- ✅ Windows va Linux uchun to'liq qo'llab-quvvatlash
- ✅ GPU device ID config orqali sozlanadi
- ✅ Index avtomatik GPU ga transfer qilinadi

### 4. GPU Monitoring
- ✅ nvidia-smi orqali GPU monitoring (Windows va Linux)
- ✅ GPU utilization, memory va temperature tracking
- ✅ Real-time GPU status loglari

## 🚀 Tez Boshlash

### Windows

```powershell
# 1. CUDA Toolkit o'rnatish
# https://developer.nvidia.com/cuda-downloads

# 2. Avtomatik sozlash
cd backend
.\scripts\setup_cuda.ps1

# 3. YANGI TERMINAL OCHING!
.\env\Scripts\Activate.ps1
python scripts/check_gpu.py

# 4. Backend ishga tushirish
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Linux

```bash
# 1. CUDA Toolkit o'rnatish
# Ubuntu/Debian:
sudo apt-get install cuda-toolkit-12-4

# 2. Environment variables
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_HOME=/usr/local/cuda

# 3. Dependencies
cd backend
source env/bin/activate
pip install -r requirements.txt

# 4. GPU tekshiruv
python scripts/check_gpu.py

# 5. Backend ishga tushirish
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 Batafsil Hujjatlar

- **Windows uchun**: [GPU_WINDOWS_SETUP.md](GPU_WINDOWS_SETUP.md)
- **Linux uchun**: [GPU_LINUX_SETUP.md](GPU_LINUX_SETUP.md)

## ⚙️ Configuration

`app/core/config.py` da GPU sozlamalari:

```python
REQUIRE_GPU: bool = False  # True = GPU majburiy (CPU fallback yo'q)
GPU_DEVICE_ID: int = 0  # GPU device ID (0 = birinchi GPU)
GPU_BATCH_SIZE: int = 8  # Batch size (katta = yaxshi GPU utilization)
GPU_MEMORY_LIMIT_GB: int = 2  # GPU memory limit (0 = cheksiz)
```

### Environment Variables

**Windows (PowerShell):**
```powershell
$env:REQUIRE_GPU="true"
$env:GPU_DEVICE_ID="0"
$env:GPU_BATCH_SIZE="16"
$env:GPU_MEMORY_LIMIT_GB="4"
```

**Linux/Mac:**
```bash
export REQUIRE_GPU=true
export GPU_DEVICE_ID=0
export GPU_BATCH_SIZE=16
export GPU_MEMORY_LIMIT_GB=4
```

## 🔍 GPU Tekshiruv

```bash
# Windows
python scripts/check_gpu.py

# Linux
python scripts/check_gpu.py
```

Bu quyidagilarni tekshiradi:
- ✅ GPU/Driver mavjudligi
- ✅ CUDA Libraries (Windows DLL yoki Linux .so)
- ✅ ONNX Runtime GPU support
- ✅ FAISS GPU support

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

Backend endi **Windows va Linux da to'liq GPU qo'llab-quvvatlash** bilan ishlaydi:
- ✅ ONNX Runtime GPU (Face Recognition)
- ✅ FAISS GPU (Vector Search)
- ✅ GPU Monitoring
- ✅ Automatic GPU detection (Windows va Linux)
- ✅ CPU fallback (agar GPU topilmasa)
- ✅ Platforma-agnostic kod

## 🔧 Troubleshooting

### Umumiy muammolar

1. **GPU topilmayapti:**
   - `nvidia-smi` ishlayotganini tekshiring
   - CUDA Toolkit o'rnatilganligini tekshiring
   - Yangi terminal oching (PATH o'zgarishlari uchun)

2. **ONNX Runtime GPU ishlamayapti:**
   - CUDA libraries PATH da ekanligini tekshiring
   - `onnxruntime-gpu` to'g'ri o'rnatilganligini tekshiring

3. **FAISS GPU ishlamayapti:**
   - `faiss-gpu` o'rnatilganligini tekshiring
   - Windows da conda orqali o'rnatish tavsiya etiladi

Batafsil ma'lumot uchun platforma-spetsifik hujjatlarga qarang:
- Windows: [GPU_WINDOWS_SETUP.md](GPU_WINDOWS_SETUP.md)
- Linux: [GPU_LINUX_SETUP.md](GPU_LINUX_SETUP.md)

