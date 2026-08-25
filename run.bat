@echo off
setlocal

title LightShare V1.0 - Desktop App
color 0b
cls

echo.
echo ========================================================================
echo    [APP] LIGHTSHARE V1.0 - DESKTOP GUI APP (CHROME RUNNER)
echo    High-Speed 30GB+ Local and Hotspot File Sharing (0 Data Usage)
echo ========================================================================
echo.

cd /d "%~dp0"

echo [1] Checking Python installation...
python --version 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python not found.
    echo Please install Python 3.10 or higher from https://www.python.org/downloads
    echo.
    cmd /k
    exit /b 1
)

echo [2] Checking Virtual Environment...
if not exist "venv" (
    echo [*] Creating fresh virtual environment...
    python -m venv venv 2>nul
)

call venv\Scripts\activate.bat 2>nul
if %errorlevel% neq 0 (
    echo [*] Rebuilding environment...
    rmdir /s /q venv 2>nul
    python -m venv venv 2>nul
    call venv\Scripts\activate.bat 2>nul
)

echo [3] Installing dependencies...
python -m pip install -r requirements.txt >nul 2>&1

:: Free port 53317 if occupied
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :53317') do taskkill /F /PID %%a >nul 2>&1

echo.
echo [*] Launching LightShare in Google Chrome App Window...
echo.

python desktop_app.py

if %errorlevel% neq 0 (
    echo [*] Desktop GUI closed. Running server in terminal mode...
    python -m app.main
)

cmd /k