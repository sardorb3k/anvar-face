# FAISS GPU O'rnatish Yo'riqnomasi

## Muammo
`ModuleNotFoundError: No module named 'faiss'` - FAISS moduli topilmadi.

## Yechim

### 1. Virtual Environment ni aktivlashtirish

PowerShell da:

```powershell
cd D:\aaa\backend
.\env\Scripts\Activate.ps1
```

Yoki Command Prompt da:

```cmd
cd D:\aaa\backend
env\Scripts\activate.bat
```

### 2. FAISS GPU ni o'rnatish

Virtual environment aktiv bo'lganda:

```powershell
# Avval eski versiyalarni o'chirish
pip uninstall faiss-cpu faiss-gpu -y

# FAISS GPU ni o'rnatish (Windows uchun)
pip install faiss-gpu==1.7.4
```

**MUAMMO:** Agar `faiss-gpu` Windows da o'rnatilmagan bo'lsa (CUDA toolkit yo'q bo'lsa), quyidagilardan birini qiling:

#### Variant A: Conda orqali o'rnatish (tavsiya etiladi)

```powershell
# Conda o'rnatilgan bo'lishi kerak
conda install -c pytorch faiss-gpu
```

#### Variant B: CPU versiyasini ishlatish (vaqtinchalik)

Agar GPU o'rnatish qiyin bo'lsa, vaqtinchalik CPU versiyasini ishlatishingiz mumkin:

```powershell
pip install faiss-cpu==1.7.4
```

Lekin bu sekinroq ishlaydi. GPU ni keyinroq o'rnatish mumkin.

### 3. Tekshirish

```powershell
python -c "import faiss; print('FAISS version:', faiss.__version__); print('GPUs:', faiss.get_num_gpus())"
```

## Muammolar va Yechimlar

### Muammo 1: "No module named 'faiss'"

**Yechim:** Virtual environment ni aktivlashtiring va FAISS ni o'rnating.

### Muammo 2: "faiss-gpu o'rnatilmayapti" (Windows)

**Yechim:** 
- CUDA Toolkit o'rnatilganligini tekshiring
- Yoki Conda orqali o'rnating: `conda install -c pytorch faiss-gpu`
- Yoki vaqtinchalik CPU versiyasini ishlating

### Muammo 3: CUDA Toolkit yo'q

**Yechim:** 
1. CUDA Toolkit 12.x ni o'rnating: https://developer.nvidia.com/cuda-downloads
2. PATH ga qo'shing: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin`
3. Ilovani qayta ishga tushiring

## Tezkor Yechim (CPU Fallback)

Agar GPU ni o'rnatishda muammo bo'lsa, vaqtinchalik CPU versiyasini ishlatishingiz mumkin:

```powershell
cd D:\aaa\backend
.\env\Scripts\Activate.ps1
pip install faiss-cpu==1.7.4
```

Lekin eslang: CPU versiyasi sekinroq ishlaydi. GPU ni keyinroq o'rnatishni tavsiya etamiz.

