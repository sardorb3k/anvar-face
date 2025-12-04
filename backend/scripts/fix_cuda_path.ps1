# CUDA PATH Sozlash - Soddalashtirilgan Skript
# Bu skript CUDA 13.0 ni PATH ga qo'shadi

Write-Host "CUDA PATH Sozlash..." -ForegroundColor Cyan

$cudaBinPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0\bin"
$cudaPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0"

# PATH ga qo'shish
Write-Host "PATH ga qo'shilmoqda..." -ForegroundColor Yellow
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$cudaBinPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$cudaBinPath", "User")
    Write-Host "OK: PATH ga qo'shildi" -ForegroundColor Green
} else {
    Write-Host "OK: PATH da allaqachon mavjud" -ForegroundColor Green
}

# CUDA_PATH o'rnatish
Write-Host "CUDA_PATH o'rnatilmoqda..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("CUDA_PATH", $cudaPath, "User")
Write-Host "OK: CUDA_PATH o'rnatildi" -ForegroundColor Green

# Session PATH ga qo'shish
$env:Path = "$env:Path;$cudaBinPath"
$env:CUDA_PATH = $cudaPath

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "OK: CUDA sozlandi!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "MUHIM: Yangi terminal oynasini oching!" -ForegroundColor Yellow
Write-Host ""

