# CUDA Toolkit Setup Script for Windows
# Bu skript CUDA Toolkit o'rnatish va PATH sozlashni osonlashtiradi

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CUDA Toolkit Setup Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. CUDA Toolkit mavjudligini tekshirish
Write-Host "1. CUDA Toolkit mavjudligini tekshirish..." -ForegroundColor Yellow

$cudaPaths = @(
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.3",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
)

$foundCuda = $null
$foundPath = $null

foreach ($path in $cudaPaths) {
    if (Test-Path $path) {
        $binPath = Join-Path $path "bin"
        # Check for both 12.x and 13.x DLL names
        $dll12 = Join-Path $binPath "cublasLt64_12.dll"
        $dll13 = Join-Path $binPath "cublasLt64_13.dll"
        
        if (Test-Path $dll13) {
            $foundCuda = $path
            $foundPath = $binPath
            Write-Host "   ✓ CUDA Toolkit topildi: $path (v13.0)" -ForegroundColor Green
            break
        } elseif (Test-Path $dll12) {
            $foundCuda = $path
            $foundPath = $binPath
            Write-Host "   ✓ CUDA Toolkit topildi: $path (v12.x)" -ForegroundColor Green
            break
        }
    }
}

if (-not $foundCuda) {
    Write-Host "   ✗ CUDA Toolkit topilmadi!" -ForegroundColor Red
    Write-Host ""
    Write-Host "YECHIM:" -ForegroundColor Yellow
    Write-Host "1. CUDA Toolkit 12.x yoki 13.x ni o'rnating:" -ForegroundColor White
    Write-Host "   https://developer.nvidia.com/cuda-downloads" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. O'rnatgandan keyin, bu skriptni qayta ishga tushiring" -ForegroundColor White
    Write-Host ""
    exit 1
}

# 2. PATH ga qo'shish
Write-Host ""
Write-Host "2. PATH ga CUDA bin papkasini qo'shish..." -ForegroundColor Yellow

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$foundPath*") {
    Write-Host "   PATH ga qo'shilmoqda..." -ForegroundColor Yellow
    
    # User PATH ga qo'shish
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$foundPath", "User")
    
    # Session PATH ga ham qo'shish
    $env:Path = "$env:Path;$foundPath"
    
    Write-Host "   ✓ PATH ga qo'shildi: $foundPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "   ⚠ MUHIM: Yangi terminal oynasini oching yoki ilovani qayta ishga tushiring!" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ PATH da allaqachon mavjud" -ForegroundColor Green
}

# 3. CUDA_PATH environment variable
Write-Host ""
Write-Host "3. CUDA_PATH environment variable sozlash..." -ForegroundColor Yellow

$cudaPath = [Environment]::GetEnvironmentVariable("CUDA_PATH", "User")
if (-not $cudaPath -or $cudaPath -ne $foundCuda) {
    [Environment]::SetEnvironmentVariable("CUDA_PATH", $foundCuda, "User")
    $env:CUDA_PATH = $foundCuda
    Write-Host "   ✓ CUDA_PATH o'rnatildi: $foundCuda" -ForegroundColor Green
} else {
    Write-Host "   ✓ CUDA_PATH allaqachon sozlangan" -ForegroundColor Green
}

# 4. Tekshirish
Write-Host ""
Write-Host "4. Tekshirish..." -ForegroundColor Yellow

$testDll12 = Join-Path $foundPath "cublasLt64_12.dll"
$testDll13 = Join-Path $foundPath "cublasLt64_13.dll"
if (Test-Path $testDll13) {
    Write-Host "   ✓ cublasLt64_13.dll topildi (CUDA 13.0)" -ForegroundColor Green
} elseif (Test-Path $testDll12) {
    Write-Host "   ✓ cublasLt64_12.dll topildi (CUDA 12.x)" -ForegroundColor Green
} else {
    Write-Host "   ✗ CUDA DLL topilmadi!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ CUDA Toolkit sozlandi!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Keyingi qadamlar:" -ForegroundColor Yellow
Write-Host "1. Yangi terminal oynasini oching" -ForegroundColor White
Write-Host "2. Virtual environment ni aktivlashtiring" -ForegroundColor White
Write-Host "3. Backend ni qayta ishga tushiring" -ForegroundColor White
Write-Host ""
Write-Host "Tekshirish uchun:" -ForegroundColor Yellow
Write-Host "   python scripts/check_gpu.py" -ForegroundColor Cyan
Write-Host ""

