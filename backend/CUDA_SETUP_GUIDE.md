# CUDA Toolkit O'rnatish va Sozlash Yo'riqnomasi

## ⚠️ Muammo

```
MUAMMO: cublasLt64_12.dll topilmayapti (CUDA Toolkit o'rnatilmagan)
```

Bu xato CUDA Toolkit o'rnatilmaganligini ko'rsatadi. GPU dan foydalanish uchun CUDA Toolkit kerak.

## ✅ Yechim

### Variant 1: Avtomatik Sozlash (Tavsiya etiladi)

PowerShell da quyidagi skriptni ishga tushiring:

```powershell
cd D:\aaa\backend
.\scripts\setup_cuda.ps1
```

Bu skript:
- CUDA Toolkit mavjudligini tekshiradi
- PATH ga avtomatik qo'shadi
- CUDA_PATH environment variable o'rnatadi

### Variant 2: Qo'lda O'rnatish

#### 1-qadam: CUDA Toolkit O'rnatish

1. CUDA Toolkit 12.x ni yuklab oling:
   - https://developer.nvidia.com/cuda-downloads
   - Windows x64 installer ni tanlang
   - Eng so'nggi versiyani o'rnating (12.4 yoki 12.3)

2. O'rnatish jarayonida:
   - Default sozlamalarni qoldiring
   - O'rnatish tugaguncha kutib turing

#### 2-qadam: PATH ga Qo'shish

**PowerShell orqali:**

```powershell
# CUDA bin papkasini toping (masalan)
$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"

# PATH ga qo'shish (User PATH)
[Environment]::SetEnvironmentVariable("Path", "$env:Path;$cudaPath", "User")

# Session PATH ga ham qo'shish
$env:Path = "$env:Path;$cudaPath"
```

**Yoki Environment Variables orqali:**

1. `Win + R` bosib, `sysdm.cpl` yozing
2. "Advanced" tab → "Environment Variables"
3. "User variables" da "Path" ni tanlang → "Edit"
4. "New" bosib, quyidagini qo'shing:
   ```
   C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin
   ```
5. "OK" bosib saqlang

#### 3-qadam: CUDA_PATH Environment Variable

1. "Environment Variables" oynasida
2. "User variables" da "New" bosib:
   - Variable name: `CUDA_PATH`
   - Variable value: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4`
3. "OK" bosib saqlang

#### 4-qadam: Tekshirish

**Yangi terminal oynasini oching** va tekshiring:

```powershell
# CUDA DLL topilishini tekshirish
Test-Path "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin\cublasLt64_12.dll"

# PATH da borligini tekshirish
$env:Path -like "*CUDA*"

# CUDA_PATH tekshirish
$env:CUDA_PATH
```

## 🔄 Keyingi Qadamlar

### 1. Yangi Terminal Ochiish

**MUHIM:** PATH o'zgarishlari yangi terminal oynasida ko'rinadi!

1. Hozirgi terminal oynasini yoping
2. Yangi PowerShell/CMD oynasini oching
3. Virtual environment ni aktivlashtiring

### 2. GPU Tekshiruv

```powershell
cd D:\aaa\backend
.\env\Scripts\Activate.ps1
python scripts/check_gpu.py
```

Agar hamma narsa to'g'ri bo'lsa, quyidagilar ko'rinadi:
```
✓ CUDAExecutionProvider MAVJUD
✓ GPU ishlatishga tayyor!
```

### 3. Backendni Ishga Tushirish

```powershell
# To'g'ri sintaksis
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Yoki skript orqali
.\start_server.ps1
```

## ⚠️ Muammolar va Yechimlar

### Muammo 1: "cublasLt64_12.dll topilmayapti"

**Yechim:**
- CUDA Toolkit o'rnatilganligini tekshiring
- PATH ga qo'shilganligini tekshiring
- Yangi terminal oynasini oching

### Muammo 2: "PATH ga qo'shildi, lekin ishlamayapti"

**Yechim:**
- Yangi terminal oynasini oching (PATH o'zgarishlari yangi session da ko'rinadi)
- Ilovani qayta ishga tushiring
- Kompyuterni qayta ishga tushiring (agar kerak bo'lsa)

### Muammo 3: "CUDA Toolkit o'rnatilgan, lekin topilmayapti"

**Yechim:**
- CUDA versiyasini tekshiring: `nvidia-smi`
- To'g'ri papkada ekanligini tekshiring
- `setup_cuda.ps1` skriptini ishga tushiring

## 📝 CPU Fallback

Agar GPU o'rnatish qiyin bo'lsa, backend CPU da ham ishlaydi:

```powershell
# CPU fallback avtomatik ishlaydi
# Faqat ogohlantirish ko'rinadi:
# "⚠ GPU topilmadi, CPU fallback ishlatiladi (sekin ishlaydi)"
```

Lekin eslang: CPU versiyasi sekinroq ishlaydi!

## ✅ Tekshiruv Ro'yxati

- [ ] CUDA Toolkit o'rnatildi
- [ ] PATH ga qo'shildi
- [ ] CUDA_PATH environment variable o'rnatildi
- [ ] Yangi terminal ochildi
- [ ] `python scripts/check_gpu.py` muvaffaqiyatli
- [ ] Backend GPU da ishlayapti

## 🎯 Xulosa

CUDA Toolkit o'rnatgandan keyin:
1. Yangi terminal oching
2. Virtual environment ni aktivlashtiring
3. `python scripts/check_gpu.py` ni ishga tushiring
4. Backend ni qayta ishga tushiring

GPU endi ishlaydi! 🚀

