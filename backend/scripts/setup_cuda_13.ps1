# CUDA 13.0 Avtomatik Sozlash Skripti
# Bu skript CUDA 13.0 ni avtomatik topadi va PATH ga qo'shadi

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CUDA 13.0 Avtomatik Sozlash" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0"
$binPath = Join-Path $cudaPath "bin"

# 1. CUDA 13.0 mavjudligini tekshirish
Write-Host "1. CUDA 13.0 mavjudligini tekshirish..." -ForegroundColor Yellow

if (-not (Test-Path $cudaPath)) {
    Write-Host "   XATO: CUDA 13.0 topilmadi: $cudaPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "   CUDA 13.0 quyidagi papkada bo'lishi kerak:" -ForegroundColor Yellow
    Write-Host "   $cudaPath" -ForegroundColor Cyan
    exit 1
}

Write-Host "   OK: CUDA 13.0 papkasi topildi: $cudaPath" -ForegroundColor Green

# 2. bin papkasini tekshirish
if (-not (Test-Path $binPath)) {
    Write-Host "   XATO: bin papkasi topilmadi!" -ForegroundColor Red
    exit 1
}

Write-Host "   OK: bin papkasi topildi: $binPath" -ForegroundColor Green

# 3. DLL fayllarini tekshirish
Write-Host ""
Write-Host "2. DLL fayllarini tekshirish..." -ForegroundColor Yellow

$dll13 = Join-Path $binPath "cublasLt64_13.dll"
$dll12 = Join-Path $binPath "cublasLt64_12.dll"

if (Test-Path $dll13) {
    Write-Host "   OK: cublasLt64_13.dll topildi (CUDA 13.0)" -ForegroundColor Green
} elseif (Test-Path $dll12) {
    Write-Host "   OK: cublasLt64_12.dll topildi (backward compatibility)" -ForegroundColor Green
} else {
    Write-Host "   WARNING: CUDA DLL topilmadi, lekin davom etamiz..." -ForegroundColor Yellow
}

# 4. PATH ga qo'shish
Write-Host ""
Write-Host "3. PATH ga qo'shish..." -ForegroundColor Yellow

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$binPath*") {
    Write-Host "   PATH ga qo'shilmoqda..." -ForegroundColor Yellow
    
    # User PATH ga qo'shish
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$binPath", "User")
    
    # Session PATH ga ham qo'shish
    $env:Path = "$env:Path;$binPath"
    
    Write-Host "   OK: PATH ga qo'shildi: $binPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "   MUHIM: Yangi terminal oynasini oching!" -ForegroundColor Yellow
} else {
    Write-Host "   OK: PATH da allaqachon mavjud" -ForegroundColor Green
}

# 5. CUDA_PATH environment variable
Write-Host ""
Write-Host "4. CUDA_PATH environment variable sozlash..." -ForegroundColor Yellow

$existingCudaPath = [Environment]::GetEnvironmentVariable("CUDA_PATH", "User")
if (-not $existingCudaPath -or $existingCudaPath -ne $cudaPath) {
    [Environment]::SetEnvironmentVariable("CUDA_PATH", $cudaPath, "User")
    $env:CUDA_PATH = $cudaPath
    Write-Host "   OK: CUDA_PATH o'rnatildi: $cudaPath" -ForegroundColor Green
} else {
    Write-Host "   OK: CUDA_PATH allaqachon sozlangan: $existingCudaPath" -ForegroundColor Green
}

# 6. Tekshirish
Write-Host ""
Write-Host "5. Final tekshirish..." -ForegroundColor Yellow

$testPath = $env:Path -like "*$binPath*"
if ($testPath) {
    Write-Host "   OK: PATH da mavjud" -ForegroundColor Green
} else {
    Write-Host "   WARNING: PATH da ko'rinmayapti (yangi terminal kerak)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OK: CUDA 13.0 sozlandi!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Keyingi qadamlar:" -ForegroundColor Yellow
Write-Host "1. YANGI TERMINAL OYNASINI OCHING!" -ForegroundColor Red -BackgroundColor Yellow
Write-Host "2. Virtual environment ni aktivlashtiring:" -ForegroundColor White
Write-Host "   .\env\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "3. GPU ni tekshiring:" -ForegroundColor White
Write-Host "   python scripts/check_gpu.py" -ForegroundColor Cyan
Write-Host "4. Backend ni qayta ishga tushiring" -ForegroundColor White
Write-Host ""
