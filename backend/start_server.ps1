# Backend server ishga tushirish skripti (PowerShell)
# Virtual environment ni aktivlashtirish va server ni ishga tushirish

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Server Ishga Tushirish" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Virtual environment ni aktivlashtirish
if (Test-Path "env\Scripts\Activate.ps1") {
    Write-Host "Virtual environment aktivlashtirilmoqda..." -ForegroundColor Yellow
    & .\env\Scripts\Activate.ps1
} else {
    Write-Host "XATO: Virtual environment topilmadi!" -ForegroundColor Red
    Write-Host "Iltimos, avval virtual environment yarating:" -ForegroundColor Yellow
    Write-Host "  python -m venv env" -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Backend server ishga tushirilmoqda..." -ForegroundColor Yellow
Write-Host ""

# Uvicorn ni ishga tushirish (to'g'ri sintaksis)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

