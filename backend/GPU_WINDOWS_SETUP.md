# GPU Windows Setup - To'liq GPU Qo'llab-quvvatlash

Bu backend endi **Windows da 100% GPU ishlatishga tayyor**! Barcha GPU funksiyalari Windows uchun optimallashtirildi.

## ✅ Amalga oshirilgan o'zgarishlar

### 1. Windows GPU Detection
- ✅ CUDA DLL avtomatik topiladi va PATH ga qo'shiladi
- ✅ Barcha CUDA versiyalari qo'llab-quvvatlanadi (11.8, 12.0-12.4, 13.0)
- ✅ Ko'p DLL variantlari tekshiriladi (cublasLt64_12.dll, cublasLt64_13.dll, va boshqalar)
- ✅ CUDA_PATH environment variable avtomatik sozlanadi
- ✅ Glob pattern orqali barcha cublas DLL'lar topiladi

### 2. ONNX Runtime GPU Optimizatsiyalari
- ✅ Windows DLL path'lar avtomatik topiladi
- ✅ GPU device ID config orqali sozlanadi
- ✅ GPU memory limit sozlanadi
- ✅ Maximum graph optimization yoqildi
- ✅ CUDA provider options optimallashtirildi

### 3. FAISS GPU Support
- ✅ Windows uchun FAISS GPU to'liq qo'llab-quvvatlanadi
- ✅ GPU device ID config orqali sozlanadi
- ✅ Index avtomatik GPU ga transfer qilinadi

### 4. GPU Monitoring
- ✅ nvidia-smi orqali GPU monitoring (Windows va Linux)
- ✅ GPU utilization, memory va temperature tracking
- ✅ Real-time GPU status loglari

## 📦 O'rnatish (Windows)

### 1. CUDA Toolkit o'rnatish

1. **CUDA Toolkit 12.x yoki 13.x ni yuklab oling:**
   - https://developer.nvidia.com/cuda-downloads
   - Windows x64 installer ni tanlang

2. **O'rnatish:**
   - Installer ni ishga tushiring
   - Default sozlamalar bilan o'rnating
   - O'rnatish tugagach, kompyuterni qayta ishga tushiring

3. **Avtomatik sozlash (Tavsiya etiladi):**
   ```powershell
   # PowerShell ni Administrator sifatida oching
   cd backend
   .\scripts\setup_cuda.ps1
   # yoki
   .\scripts\setup_cuda_13.ps1
   ```

### 2. Manual Sozlash (Agar kerak bo'lsa)

**PATH ga qo'shish:**
1. Windows Settings → System → About → Advanced system settings
2. Environment Variables
3. System variables → Path → Edit
4. Qo'shing: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin`
5. OK va yangi terminal oching

**CUDA_PATH environment variable:**
1. Environment Variables → New
2. Variable name: `CUDA_PATH`
3. Variable value: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4`
4. OK

### 3. Dependencies o'rnatish

```powershell
cd backend

# Virtual environment aktivlashtirish
.\env\Scripts\Activate.ps1

# GPU dependencies o'rnatish
pip install -r requirements.txt

# FAISS GPU (Windows da conda orqali yaxshiroq ishlaydi)
# Lekin pip orqali ham ishlaydi:
pip install faiss-gpu==1.7.4

# ONNX Runtime GPU
pip install onnxruntime-gpu==1.16.3
```

**ESLATMA:** Windows da `faiss-gpu` pip orqali ba'zida muammo bo'lishi mumkin. Agar muammo bo'lsa:
- Conda ishlatish tavsiya etiladi
- Yoki `faiss-cpu` ishlatish (sekinroq, lekin ishlaydi)

### 4. GPU Tekshiruv

```powershell
# GPU va CUDA tekshiruv
python scripts/check_gpu.py

# NVIDIA driverlar tekshiruv
nvidia-smi

# CUDA versiyasi tekshiruv (agar CUDA bin PATH da bo'lsa)
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

```powershell
# PowerShell
$env:REQUIRE_GPU="true"
$env:GPU_DEVICE_ID="0"
$env:GPU_BATCH_SIZE="16"
$env:GPU_MEMORY_LIMIT_GB="4"

# CMD
set REQUIRE_GPU=true
set GPU_DEVICE_ID=0
set GPU_BATCH_SIZE=16
set GPU_MEMORY_LIMIT_GB=4
```

## 🚀 Ishlatish

### Normal ishga tushirish

```powershell
cd backend
.\env\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Yoki `start_server.ps1` skriptini ishlatish:

```powershell
.\start_server.ps1
```

Backend avtomatik ravishda:
1. GPU mavjudligini tekshiradi (Windows DLL'lar)
2. GPU topilsa, GPU da ishlaydi
3. GPU topilmasa, CPU fallback (ogohlantirish bilan)

### GPU Status Loglari

Backend ishga tushganda, loglarida quyidagilar ko'rinadi:

```
✓ CUDA 12.x DLL found and added to PATH
✓ CUDAExecutionProvider is available
✓ InsightFace initialized successfully with GPU support
✓ FAISS initialized on GPU device 0 for maximum performance!
```

## 🔍 Troubleshooting

### GPU topilmayapti

1. **NVIDIA driverlar o'rnatilganligini tekshiring:**
   ```powershell
   nvidia-smi
   ```

2. **CUDA Toolkit o'rnatilganligini tekshiring:**
   ```powershell
   # CUDA bin papkasini tekshiring
   Test-Path "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin\cublasLt64_12.dll"
   ```

3. **PATH ga qo'shing:**
   ```powershell
   # Avtomatik sozlash
   .\scripts\setup_cuda.ps1
   
   # Yoki manual
   $env:Path += ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"
   ```

4. **ONNX Runtime GPU tekshiruv:**
   ```powershell
   python -c "import onnxruntime as ort; print(ort.get_available_providers())"
   ```
   `CUDAExecutionProvider` ko'rinishi kerak.

5. **YANGI TERMINAL OCHING!** PATH o'zgarishlari faqat yangi terminalda ko'rinadi.

### CUDA DLL topilmayapti

**Muammo:** `cublasLt64_12.dll topilmayapti`

**Yechim:**
1. CUDA Toolkit to'liq o'rnatilganligini tekshiring
2. Avtomatik sozlash skriptini ishlating:
   ```powershell
   .\scripts\setup_cuda.ps1
   ```
3. YANGI TERMINAL OCHING (muhim!)
4. Backend ni qayta ishga tushiring

### FAISS GPU ishlamayapti

1. **FAISS GPU o'rnatilganligini tekshiring:**
   ```powershell
   python -c "import faiss; print(faiss.get_num_gpus())"
   ```
   `1` yoki ko'proq ko'rinishi kerak.

2. **Agar 0 ko'rsatsa:**
   ```powershell
   pip uninstall faiss-cpu faiss-gpu
   pip install faiss-gpu==1.7.4
   ```

3. **Agar pip orqali ishlamasa, Conda ishlating:**
   ```powershell
   conda install -c pytorch faiss-gpu
   ```

### ONNX Runtime GPU ishlamayapti

**Muammo:** `CUDAExecutionProvider` ko'rinmayapti

**Yechim:**
1. CUDA DLL'lar PATH da ekanligini tekshiring
2. YANGI TERMINAL OCHING
3. `onnxruntime-gpu` ni qayta o'rnating:
   ```powershell
   pip uninstall onnxruntime onnxruntime-gpu
   pip install onnxruntime-gpu==1.16.3
   ```

## 📊 Performance

GPU ishlatganda:
- **Face Recognition**: 10-50x tezroq (CPU ga nisbatan)
- **Vector Search**: 5-20x tezroq (CPU ga nisbatan)
- **Batch Processing**: GPU da parallel bajariladi

## ✅ Tekshiruvlar

Barcha GPU funksiyalari to'g'ri ishlayotganini tekshirish:

```powershell
# 1. GPU tekshiruv skripti
python scripts/check_gpu.py

# 2. GPU performance test
python scripts/test_gpu_performance.py

# 3. Backend ishga tushirish va loglarni ko'rish
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🎯 Xulosa

Backend endi Windows da **to'liq GPU qo'llab-quvvatlash** bilan ishlaydi:
- ✅ ONNX Runtime GPU (Face Recognition)
- ✅ FAISS GPU (Vector Search)
- ✅ GPU Monitoring
- ✅ Automatic GPU detection
- ✅ CPU fallback (agar GPU topilmasa)
- ✅ Windows DLL avtomatik topiladi va PATH ga qo'shiladi

GPU ni majburiy qilish uchun: `$env:REQUIRE_GPU="true"`

## 📝 Qo'shimcha Eslatmalar

1. **YANGI TERMINAL:** PATH o'zgarishlaridan keyin har doim yangi terminal oching!
2. **Administrator huquqlari:** Ba'zi sozlashlar Administrator huquqlari talab qiladi
3. **CUDA versiyasi:** CUDA 12.x yoki 13.x tavsiya etiladi
4. **FAISS GPU:** Windows da conda orqali o'rnatish yaxshiroq ishlaydi

