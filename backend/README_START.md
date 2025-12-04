# Backend Ishga Tushirish - Tezkor Yo'riqnoma

## 🚀 Tezkor Start

### 1. Virtual Environment Aktivlashtirish

**PowerShell:**
```powershell
cd D:\aaa\backend
.\env\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
cd D:\aaa\backend
env\Scripts\activate.bat
```

### 2. Serverni Ishga Tushirish

**Variant A: Skript orqali (Tavsiya etiladi)**

PowerShell:
```powershell
.\start_server.ps1
```

Command Prompt:
```cmd
start_server.bat
```

**Variant B: Qo'lda**

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**⚠️ MUHIM:** `app.main.py` emas, `app.main:app` ishlatish kerak!

## ⚠️ GPU Muammosi

Agar quyidagi xato ko'rsangiz:

```
MUAMMO: cublasLt64_12.dll topilmayapti (CUDA Toolkit o'rnatilmagan)
```

**Yechim:**

1. CUDA Toolkit o'rnating: https://developer.nvidia.com/cuda-downloads
2. Avtomatik sozlash:
   ```powershell
   .\scripts\setup_cuda.ps1
   ```
3. Yangi terminal oching
4. Backend ni qayta ishga tushiring

Batafsil: `CUDA_SETUP_GUIDE.md`

## ✅ Tekshirish

Server ishga tushgandan keyin:

- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

## 📝 Qo'shimcha Ma'lumot

- `CUDA_SETUP_GUIDE.md` - CUDA o'rnatish
- `GPU_SETUP.md` - GPU optimizatsiyalari
- `FINAL_STEPS.md` - To'liq setup

