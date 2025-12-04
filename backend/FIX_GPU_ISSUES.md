# GPU Muammolarini Hal Qilish

## Muammo: CUDA DLLs va FAISS GPU topilmayapti

### 1. CUDA DLLs Muammosi

**Xato:** `✗ CUDA DLLs`

**Yechim:**

#### Variant A: Avtomatik (Tavsiya etiladi)

```powershell
cd D:\aaa\backend
.\scripts\setup_cuda_13.ps1
```

**MUHIM:** Skriptdan keyin **YANGI TERMINAL OCHING!**

#### Variant B: Qo'lda

```powershell
# PATH ga qo'shish
$cudaBinPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin"
[Environment]::SetEnvironmentVariable("Path", "$([Environment]::GetEnvironmentVariable('Path', 'User'));$cudaBinPath", "User")

# CUDA_PATH o'rnatish
[Environment]::SetEnvironmentVariable("CUDA_PATH", "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0", "User")
```

**YANGI TERMINAL OCHING!**

### 2. FAISS GPU Muammosi

**Xato:** `✗ FAISS GPU`

**Eslatma:** Bu muhim emas! FAISS CPU versiyasi ham ishlaydi.

**Yechim (ixtiyoriy):**

Windows da `faiss-gpu` pip orqali o'rnatilmaydi. Conda kerak:

```powershell
# Conda o'rnatish kerak
conda install -c pytorch faiss-gpu
```

**Lekin:** FAISS CPU versiyasi ishlaydi, faqat sekinroq. Asosiy narsa - CUDA DLLs to'g'ri ishlayotganligi!

## Tezkor Yechim

1. **YANGI TERMINAL OCHING** (muhim!)
2. PATH ga qo'shing:
   ```powershell
   cd D:\aaa\backend
   .\scripts\setup_cuda_13.ps1
   ```
3. **YANA YANGI TERMINAL OCHING**
4. Tekshiring:
   ```powershell
   python scripts/check_gpu.py
   ```

## Kutilgan Natija

```
✓ GPU/Driver
✓ CUDA DLLs          <- Bu muhim!
✓ ONNX Runtime GPU   <- Bu muhim!
✗ FAISS GPU          <- Bu OK, CPU ishlaydi
```

Agar CUDA DLLs va ONNX Runtime GPU ✓ bo'lsa, backend GPU da ishlaydi!

## Qo'shimcha Ma'lumot

- `CUDA_13_SETUP.md` - Batafsil CUDA setup
- `GPU_SETUP.md` - GPU optimizatsiyalari

