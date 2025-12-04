# CUDA DLL Muammosini Tezkor Hal Qilish

## Muammo

```
✗ CUDA DLLs
CUDA Toolkit o'rnatilmagan yoki PATH ga qo'shilmagan
```

## ✅ Tezkor Yechim

### 1-qadam: PATH ga qo'shish (PowerShell)

**Hozirgi terminal oynasida** quyidagi buyruqlarni bajarib:

```powershell
cd D:\aaa\backend

# PATH ga qo'shish
$binPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$currentPath;$binPath", "User")

# CUDA_PATH o'rnatish
[Environment]::SetEnvironmentVariable("CUDA_PATH", "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0", "User")

# Session PATH ga ham qo'shish
$env:Path = "$env:Path;$binPath"
$env:CUDA_PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0"

Write-Host "✓ CUDA 13.0 sozlandi!"
```

### 2-qadam: Yangi Terminal Oching

**MUHIM:** PATH o'zgarishlari faqat yangi terminal oynasida ko'rinadi!

1. Hozirgi terminal oynasini yoping
2. **YANGI PowerShell oynasini oching**
3. Virtual environment ni aktivlashtiring:
   ```powershell
   cd D:\aaa\backend
   .\env\Scripts\Activate.ps1
   ```

### 3-qadam: Tekshirish

Yangi terminal da:

```powershell
python scripts/check_gpu.py
```

Kutilgan natija:
```
✓ GPU/Driver
✓ CUDA DLLs          <- Endi bu ✓ bo'ladi!
✓ ONNX Runtime GPU
✗ FAISS GPU          <- Bu OK, CPU ishlaydi
```

## ⚠️ Agar Hali Ham Ishlamasa

### Variant 1: System PATH ga qo'shish

1. `Win + R` → `sysdm.cpl` yozing
2. "Advanced" → "Environment Variables"
3. "System variables" da "Path" ni tanlang → "Edit"
4. "New" bosib qo'shing:
   ```
   C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin
   ```
5. "OK" bosib saqlang
6. **Kompyuterni qayta ishga tushiring**

### Variant 2: Skript orqali

```powershell
.\scripts\setup_cuda_13.ps1
```

Va **yangi terminal oching!**

## ✅ Tekshirish

Yangi terminal da:

```powershell
# PATH da borligini tekshirish
$env:Path -like "*CUDA*v13.0*"

# CUDA_PATH tekshirish
$env:CUDA_PATH

# Python orqali tekshirish
python -c "import os; print('CUDA_PATH:', os.environ.get('CUDA_PATH')); print('PATH has CUDA:', 'CUDA' in os.environ.get('PATH', ''))"
```

## 🎯 Xulosa

1. PATH ga qo'shing (yuqoridagi buyruqlar)
2. **YANGI TERMINAL OCHING** (muhim!)
3. Tekshiring

GPU endi ishlaydi! 🚀

