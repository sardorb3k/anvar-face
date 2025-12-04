# Docker + GPU Setup (Windows)

## Talablar

1. **Windows 10/11** (21H2 yoki yuqori)
2. **Docker Desktop** (WSL2 backend bilan)
3. **NVIDIA GPU** (GTX 1060+ yoki RTX)
4. **NVIDIA Driver** (525+ versiya)

---

## 1-qadam: WSL2 va Docker Desktop sozlash

### WSL2 o'rnatish (agar yo'q bo'lsa):
```powershell
wsl --install
wsl --set-default-version 2
```

### Docker Desktop:
1. Docker Desktop o'rnating: https://docker.com/products/docker-desktop
2. Settings → General → "Use WSL 2 based engine" ✅
3. Settings → Resources → WSL Integration → Ubuntu ✅

---

## 2-qadam: NVIDIA Container Toolkit

Docker Desktop 4.29+ versiyalarda avtomatik qo'llab-quvvatlanadi.

### Tekshirish:
```powershell
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

Agar GPU ko'rinsa - tayyor!

---

## 3-qadam: Ishga tushirish

```powershell
cd backend

# Build va run
docker-compose up --build

# Background mode
docker-compose up --build -d

# Loglarni ko'rish
docker-compose logs -f
```

---

## 4-qadam: Tekshirish

### API ishlayaptimi:
```
http://localhost:8000
http://localhost:8000/docs
http://localhost:8000/health
```

### GPU ishlayaptimi:
```powershell
docker-compose exec backend python -c "
import onnxruntime
print('Providers:', onnxruntime.get_available_providers())
"
```

Natija: `['CUDAExecutionProvider', 'CPUExecutionProvider']`

---

## Foydali buyruqlar

```powershell
# Stop
docker-compose down

# Rebuild (kod o'zgarganda)
docker-compose up --build

# Loglar
docker-compose logs -f backend

# Container ichiga kirish
docker-compose exec backend bash

# GPU monitoring
docker-compose exec backend nvidia-smi

# Volume'larni tozalash
docker-compose down -v
```

---

## Xatoliklar

### "no matching manifest for windows/amd64"
→ Docker Desktop → Settings → Docker Engine:
```json
{
  "experimental": true
}
```

### GPU ko'rinmayapti
→ NVIDIA Driver yangilang (525+)
→ Docker Desktop restart qiling

### Build sekin
→ Birinchi marta ~10-15 daqiqa kutish kerak (CUDA image katta)

---

## Sozlamalar

`docker-compose.yml` ichida environment o'zgartirish mumkin:

| Sozlama | Default | Tavsif |
|---------|---------|--------|
| `CONFIDENCE_THRESHOLD` | 0.6 | Yuz aniqlash confidence |
| `MAX_FACES_PER_FRAME` | 20 | Bir kadrda max yuzlar |
| `COOLDOWN_SECONDS` | 10 | Takroriy aniqlash oralig'i |
| `GPU_MEMORY_LIMIT_GB` | 4 | GPU memory limit |
