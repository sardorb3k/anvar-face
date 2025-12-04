# CUDA 13.0 Sozlash - Tezkor Yo'riqnoma

## ✅ CUDA 13.0 Topilgan!

CUDA 13.0 quyidagi papkada joylashgan:
```
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin
```

## 🚀 Avtomatik Sozlash

PowerShell da quyidagi skriptni ishga tushiring:

```powershell
cd D:\aaa\backend
.\scripts\setup_cuda_13.ps1
```

Bu skript:
- ✅ CUDA 13.0 papkasini tekshiradi
- ✅ PATH ga avtomatik qo'shadi
- ✅ CUDA_PATH environment variable o'rnatadi

## 📝 Qo'lda Sozlash

Agar skript ishlamasa, qo'lda qiling:

### 1. PATH ga Qo'shish (PowerShell)

```powershell
# PATH ga qo'shish
$cudaBinPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin"
[Environment]::SetEnvironmentVariable("Path", "$env:Path;$cudaBinPath", "User")
$env:Path = "$env:Path;$cudaBinPath"

# CUDA_PATH o'rnatish
[Environment]::SetEnvironmentVariable("CUDA_PATH", "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0", "User")
$env:CUDA_PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0"
```

### 2. Environment Variables orqali

1. `Win + R` → `sysdm.cpl` yozing
2. "Advanced" tab → "Environment Variables"
3. "User variables" da "Path" ni tanlang → "Edit"
4. "New" bosib, quyidagini qo'shing:
   ```
   C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin
   ```
5. "New" bosib, CUDA_PATH qo'shing:
   - Variable name: `CUDA_PATH`
   - Variable value: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0`
6. "OK" bosib saqlang

## 🔄 Keyingi Qadamlar

### 1. YANGI TERMINAL OCHING!

**MUHIM:** PATH o'zgarishlari faqat yangi terminal oynasida ko'rinadi!

### 2. GPU Tekshiruv

```powershell
cd D:\aaa\backend
.\env\Scripts\Activate.ps1
python scripts/check_gpu.py
```

Agar hamma narsa to'g'ri bo'lsa:
```
✓ CUDAExecutionProvider MAVJUD
✓ GPU ishlatishga tayyor!
```

### 3. Backendni Ishga Tushirish

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## ✅ Tekshirish

Yangi terminal da tekshiring:

```powershell
# PATH da borligini tekshirish
$env:Path -like "*CUDA*v13.0*"

# CUDA_PATH tekshirish
$env:CUDA_PATH

# DLL topilishini tekshirish
Test-Path "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin\cublasLt64_13.dll"
```

## 🎯 Xulosa

CUDA 13.0 sozlandi! Endi:
1. Yangi terminal oching
2. GPU ni tekshiring
3. Backend ni qayta ishga tushiring

GPU endi ishlaydi! 🚀

