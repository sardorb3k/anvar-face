@echo off
REM Backend server ishga tushirish skripti
REM Virtual environment ni aktivlashtirish va server ni ishga tushirish

echo ========================================
echo Backend Server Ishga Tushirish
echo ========================================
echo.

REM Virtual environment ni aktivlashtirish
if exist "env\Scripts\activate.bat" (
    echo Virtual environment aktivlashtirilmoqda...
    call env\Scripts\activate.bat
) else (
    echo XATO: Virtual environment topilmadi!
    echo Iltimos, avval virtual environment yarating:
    echo   python -m venv env
    pause
    exit /b 1
)

echo.
echo Backend server ishga tushirilmoqda...
echo.

REM Uvicorn ni ishga tushirish (to'g'ri sintaksis)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause

